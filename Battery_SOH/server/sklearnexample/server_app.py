


"""sklearnexample: Flower Server with Prometheus metrics and InfluxDB persistence"""

from typing import Dict, List, Tuple, Optional
import os
from datetime import datetime, timezone

from flwr.common import Context, Metrics, Scalar, ndarrays_to_parameters
from flwr.server import ServerApp, ServerAppComponents, ServerConfig
from flwr.server.strategy import FedAvg
from prometheus_client import start_http_server, Gauge
import numpy as np
import flwr as fl

# InfluxDB client for persistent metrics storage
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

from sklearnexample.task import (
    UNIQUE_LABELS,
    create_log_reg_and_instantiate_parameters,
    get_model_parameters,
    load_data,
    set_model_params,
    central_evaluate
)
from sklearnexample.fl_analytics import get_analytics, reset_analytics


# ===========================================================
# INFLUXDB CONFIGURATION
# ===========================================================

INFLUXDB_URL = os.getenv("INFLUXDB_URL", "http://fl-influxdb:8086")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN", "fl-simulator-token-2025")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG", "flower")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET", "fl-metrics")

# Global InfluxDB client
_influx_client: Optional[InfluxDBClient] = None
_write_api = None


def _init_influxdb():
    """Initialize InfluxDB client."""
    global _influx_client, _write_api
    if os.getenv("DISABLE_INFLUXDB"):
        print("[INFLUXDB] Disabled via environment variable")
        return
    try:
        _influx_client = InfluxDBClient(
            url=INFLUXDB_URL,
            token=INFLUXDB_TOKEN,
            org=INFLUXDB_ORG
        )
        _write_api = _influx_client.write_api(write_options=SYNCHRONOUS)
        # Test connection
        health = _influx_client.health()
        print(f"[INFLUXDB] Connected to {INFLUXDB_URL} - Status: {health.status}")
    except Exception as e:
        print(f"[INFLUXDB] Failed to connect: {e}")
        _influx_client = None
        _write_api = None


def write_to_influxdb(measurement: str, fields: Dict[str, float], tags: Optional[Dict[str, str]] = None):
    """Write a data point to InfluxDB."""
    if _write_api is None:
        return
    try:
        point = Point(measurement)
        if tags:
            for key, value in tags.items():
                point = point.tag(key, value)
        for key, value in fields.items():
            point = point.field(key, float(value))
        point = point.time(datetime.now(timezone.utc), WritePrecision.NS)
        _write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)
    except Exception as e:
        print(f"[INFLUXDB] Write error: {e}")


def write_analytics_to_influxdb(measurement: str, fields: Dict[str, str], tags: Optional[Dict[str, str]] = None):
    """Write text analytics to InfluxDB (supports string fields)."""
    if _write_api is None:
        return
    try:
        point = Point(measurement)
        if tags:
            for key, value in tags.items():
                point = point.tag(key, str(value))
        for key, value in fields.items():
            point = point.field(key, str(value))
        point = point.time(datetime.now(timezone.utc), WritePrecision.NS)
        _write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)
    except Exception as e:
        print(f"[INFLUXDB] Analytics write error: {e}")


# Initialize InfluxDB on module load
_init_influxdb()


# ===========================================================
# PROMETHEUS METRICS
# ===========================================================

def _start_prometheus(port: int = 8001):
    """Start Prometheus metrics endpoint."""
    if os.getenv("DISABLE_PROMETHEUS"):
        return
    start_http_server(port)
    print(f"Prometheus server running at http://0.0.0.0:{port}/metrics")


# Start Prometheus server
_start_prometheus(port=int(os.getenv("SERVER_METRICS_PORT", "8001")))

# ---- Global aggregated metrics ----
SERVER_ROUND = Gauge("fl_server_round", "Current federated learning round")
SERVER_AGG_TRAIN_R2 = Gauge("fl_server_aggregated_train_r2", "Aggregated train R²")
SERVER_AGG_TEST_R2 = Gauge("fl_server_aggregated_test_r2", "Aggregated test R²")
SERVER_AGG_LOSS = Gauge("fl_server_aggregated_loss", "Aggregated test loss")


SERVER_CENTRAL_EVAL_R2 = Gauge("fl_server_cetral_evaluation_R2", "central evaluation r2")
SERVER_CENTRAL_EVAL_LOSS = Gauge("fl_server_cetral_evaluation_loss", "central evaluation loss")

# ---- Per-client metrics (SEPARATE) ----
CLIENT_TRAIN_R2 = Gauge("fl_client_train_r2","Client training R²",["client_id"],)
CLIENT_TEST_R2 = Gauge("fl_client_test_r2","Client testing R²",["client_id"],)
CLIENT_LOSS = Gauge("fl_client_loss","Client loss (MSE)",["client_id"],)

CLIENT_CPU = Gauge("fl_client_cpu_fit_percent", "CPU Percent during fit", ["client_id"])
CLIENT_CPU_TIME = Gauge("fl_client_cpu_time_usage", "CPU Time Usage", ["client_id"])

CLIENT_MEMORY = Gauge("fl_client_memory_fit_mb", "Memory MB change during fit", ["client_id"])

# Global storage for client metrics (to pass to analytics)
_current_round_client_metrics: Dict[str, Dict] = {}


# ===========================================================
# METRIC AGGREGATION
# ===========================================================

def weighted_average(metrics: List[Tuple[int, Metrics]]) -> Dict[str, Scalar]:
    """Compute weighted average and export per-client metrics separately."""
    global _current_round_client_metrics

    total_samples = sum(n for n, _ in metrics)
    if total_samples == 0:
        return {}

    # Initialize weighted sums
    sum_train_r2, sum_test_r2, sum_loss = 0.0, 0.0, 0.0
    stage = None
    current_round = int(SERVER_ROUND._value.get())  # Get current round for InfluxDB tags

    # Iterate over each client's metrics
    for n_samples, client_metrics in metrics:
        stage = client_metrics.get("stage", None)
        cid = client_metrics.get("cid", None)
        if cid is not None:
            client_influx_fields = {}

            if "train_r_squared" in client_metrics:
                CLIENT_TRAIN_R2.labels(client_id=str(cid)).set(
                    float(client_metrics["train_r_squared"])
                )
                client_influx_fields["train_r2"] = float(client_metrics["train_r_squared"])
            if "test_r_squared" in client_metrics:
                CLIENT_TEST_R2.labels(client_id=str(cid)).set(
                    float(client_metrics["test_r_squared"])
                )
                client_influx_fields["test_r2"] = float(client_metrics["test_r_squared"])
            if "loss" in client_metrics:
                CLIENT_LOSS.labels(client_id=str(cid)).set(
                    float(client_metrics["loss"])
                )
                client_influx_fields["loss"] = float(client_metrics["loss"])
            if "cpu_percent_fit" in client_metrics:
                CLIENT_CPU.labels(client_id=str(cid)).set(client_metrics["cpu_percent_fit"])
                client_influx_fields["cpu_percent"] = float(client_metrics["cpu_percent_fit"])

            if "memory_mb_fit" in client_metrics:
                CLIENT_MEMORY.labels(client_id=str(cid)).set(client_metrics["memory_mb_fit"])
                client_influx_fields["memory_mb"] = float(client_metrics["memory_mb_fit"])

            if "cpu_time_sec" in client_metrics:
                CLIENT_CPU_TIME.labels(client_id=str(cid)).set(client_metrics["cpu_time_sec"])
                client_influx_fields["cpu_time_sec"] = float(client_metrics["cpu_time_sec"])

            # Write client metrics to InfluxDB
            if client_influx_fields:
                write_to_influxdb(
                    "fl_client_metrics",
                    client_influx_fields,
                    tags={"client_id": str(cid), "round": str(current_round), "stage": str(stage)}
                )
                # Store for analytics
                _current_round_client_metrics[str(cid)] = client_influx_fields.copy()

        # Add weighted sums for aggregation
        if "train_r_squared" in client_metrics:
            sum_train_r2 += client_metrics["train_r_squared"] * n_samples
        if "test_r_squared" in client_metrics:
            sum_test_r2 += client_metrics["test_r_squared"] * n_samples
        if "loss" in client_metrics:
            sum_loss += client_metrics["loss"] * n_samples

    # Compute aggregated averages
    if stage == "fit":
        aggregated = {
            "train_r_squared": sum_train_r2 / total_samples,

        }
        SERVER_AGG_TRAIN_R2.set(aggregated["train_r_squared"])

        # Write aggregated fit metrics to InfluxDB
        write_to_influxdb(
            "fl_server_metrics",
            {"aggregated_train_r2": aggregated["train_r_squared"]},
            tags={"round": str(current_round), "stage": "fit"}
        )

    else:
        aggregated = {
            "test_r_squared": sum_test_r2 / total_samples,
            "loss": sum_loss / total_samples,
        }
        SERVER_AGG_TEST_R2.set(aggregated["test_r_squared"])
        SERVER_AGG_LOSS.set(aggregated["loss"])

        # Write aggregated eval metrics to InfluxDB
        write_to_influxdb(
            "fl_server_metrics",
            {
                "aggregated_test_r2": aggregated["test_r_squared"],
                "aggregated_loss": aggregated["loss"]
            },
            tags={"round": str(current_round), "stage": "evaluate"}
        )

    print(f"[SERVER] Aggregated metrics → {aggregated}")
    return aggregated

def evaluate_fn(server_round, parameters, config):
    """Centralized evaluation with analytics generation."""
    global _current_round_client_metrics

    # CALL the centralized eval from task.py
    loss, metrics = central_evaluate(server_round, parameters, config)

    # NOW you have the values right here:
    test_r2 = metrics.get("r2")

    print("[SERVER] Central evaluation:", metrics)
    SERVER_CENTRAL_EVAL_R2.set(test_r2)
    SERVER_CENTRAL_EVAL_LOSS.set(loss)

    # Write central evaluation metrics to InfluxDB
    write_to_influxdb(
        "fl_central_evaluation",
        {
            "r2": float(test_r2) if test_r2 is not None else 0.0,
            "loss": float(loss)
        },
        tags={"round": str(server_round)}
    )

    # =========================================================
    # GENERATE AND STORE ANALYTICS
    # =========================================================
    analytics = get_analytics()

    # Get aggregated metrics
    aggregated_metrics = {
        "train_r2": float(SERVER_AGG_TRAIN_R2._value.get()) if SERVER_AGG_TRAIN_R2._value.get() else 0.0,
        "test_r2": float(SERVER_AGG_TEST_R2._value.get()) if SERVER_AGG_TEST_R2._value.get() else 0.0,
        "loss": float(SERVER_AGG_LOSS._value.get()) if SERVER_AGG_LOSS._value.get() else 0.0
    }

    # Analyze round
    analysis = analytics.analyze_round(
        round_num=server_round,
        central_r2=float(test_r2) if test_r2 else 0.0,
        central_loss=float(loss),
        client_metrics=_current_round_client_metrics.copy(),
        aggregated_metrics=aggregated_metrics
    )

    # Write round analytics to InfluxDB
    write_analytics_to_influxdb(
        "fl_round_analytics",
        {
            "round_summary": analysis["round_summary"],
            "model_status": analysis["model_status"],
            "convergence_analysis": analysis["convergence_analysis"],
            "recommendations": analysis["recommendations"],
            "overall_health": analysis["overall_health"]
        },
        tags={"round": str(server_round)}
    )

    # Write client analytics to InfluxDB
    for client_id, client_analysis in analysis["client_analysis"].items():
        write_analytics_to_influxdb(
            "fl_client_analytics",
            {"analysis": client_analysis},
            tags={"round": str(server_round), "client_id": client_id}
        )

    # Print analytics to console
    print(f"\n{'='*60}")
    print(f"📊 FL ANALYTICS - Round {server_round}")
    print(f"{'='*60}")
    print(f"📋 Summary: {analysis['round_summary']}")
    print(f"🤖 Model: {analysis['model_status']}")
    print(f"📈 Convergence: {analysis['convergence_analysis']}")
    print(f"💡 Recommendations: {analysis['recommendations']}")
    print(f"❤️ Health: {analysis['overall_health']}")
    print(f"{'='*60}\n")

    # Clear client metrics for next round
    _current_round_client_metrics.clear()

    # Saving the final model after each round
    ndarrays = parameters
    np.savez("/app/model/final_model.npz", *ndarrays)
    print("💾 Final model saved to saved_model/final_model.npz")

    return loss, metrics


def fit_config(server_round: int):
    SERVER_ROUND.set(server_round)
    # Write round start to InfluxDB
    write_to_influxdb(
        "fl_training_progress",
        {"round": float(server_round)},
        tags={"event": "round_start"}
    )
    return {"local_epochs": 5}

def server_fn(context: Context) -> ServerAppComponents:
    penalty = context.run_config["penalty"]

    # Initialize model
    model = create_log_reg_and_instantiate_parameters(penalty)
    ndarrays = get_model_parameters(model)
    init_params = ndarrays_to_parameters(ndarrays)

    min_clients = context.run_config["min-available-clients"]

    strategy = FedAvg(
        min_available_clients=min_clients,
        fit_metrics_aggregation_fn=weighted_average,
        evaluate_metrics_aggregation_fn=weighted_average,
        initial_parameters=init_params,
        on_fit_config_fn=fit_config,
        evaluate_fn=evaluate_fn,
    )

    num_rounds = context.run_config["num-server-rounds"]
    config = ServerConfig(num_rounds=num_rounds)


    return ServerAppComponents(strategy=strategy, config=config )

# ===========================================================
# Create the Flower ServerApp
# ===========================================================
app = ServerApp(server_fn=server_fn)
