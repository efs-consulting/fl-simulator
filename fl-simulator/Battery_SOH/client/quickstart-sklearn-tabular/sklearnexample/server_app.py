


"""sklearnexample: Flower Server with Prometheus metrics"""

from typing import Dict, List, Tuple
import os

from flwr.common import Context, Metrics, Scalar, ndarrays_to_parameters
from flwr.server import ServerApp, ServerAppComponents, ServerConfig
from flwr.server.strategy import FedAvg
from prometheus_client import start_http_server, Gauge
import flwr as fl
import numpy as np

from sklearnexample.task import (
    UNIQUE_LABELS,
    create_log_reg_and_instantiate_parameters,
    get_model_parameters,
    load_data,
    set_model_params,
    central_evaluate
)


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


# ===========================================================
# METRIC AGGREGATION
# ===========================================================

def weighted_average(metrics: List[Tuple[int, Metrics]]) -> Dict[str, Scalar]:
    """Compute weighted average and export per-client metrics separately."""

    total_samples = sum(n for n, _ in metrics)
    if total_samples == 0:
        return {}

    # Initialize weighted sums
    sum_train_r2, sum_test_r2, sum_loss = 0.0, 0.0, 0.0
    stage = None
    # Iterate over each client's metrics
    for n_samples, client_metrics in metrics:
        stage = client_metrics.get("stage", None)
        cid = client_metrics.get("cid", None)
        if cid is not None:
            if "train_r_squared" in client_metrics:
                CLIENT_TRAIN_R2.labels(client_id=str(cid)).set(
                    float(client_metrics["train_r_squared"])
                )
            if "test_r_squared" in client_metrics:
                CLIENT_TEST_R2.labels(client_id=str(cid)).set(
                    float(client_metrics["test_r_squared"])
                )
            if "loss" in client_metrics:
                CLIENT_LOSS.labels(client_id=str(cid)).set(
                    float(client_metrics["loss"])
                )
            if "cpu_percent_fit" in client_metrics:
                CLIENT_CPU.labels(client_id=str(cid)).set(client_metrics["cpu_percent_fit"])

            if "memory_mb_fit" in client_metrics:
                CLIENT_MEMORY.labels(client_id=str(cid)).set(client_metrics["memory_mb_fit"])

            if "cpu_time_sec" in client_metrics:
                CLIENT_CPU_TIME.labels(client_id=str(cid)).set(client_metrics["cpu_time_sec"])

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

    else:
        aggregated = {
            "test_r_squared": sum_test_r2 / total_samples,
            "loss": sum_loss / total_samples,
        }
        SERVER_AGG_TEST_R2.set(aggregated["test_r_squared"])
        SERVER_AGG_LOSS.set(aggregated["loss"])
        

    # Update Prometheus aggregated metrics
    

    print(f"[SERVER] Aggregated metrics → {aggregated}")
    return aggregated

def evaluate_fn(server_round, parameters, config):
    # CALL the centralized eval from task.py
    loss, metrics = central_evaluate(server_round, parameters, config)

    # NOW you have the values right here:
    test_r2 = metrics.get("r2")

    

    print("[SERVER] Central evaluation:", metrics)
    SERVER_CENTRAL_EVAL_R2.set(test_r2)
    SERVER_CENTRAL_EVAL_LOSS.set(loss)
    
    return loss, metrics


def fit_config(server_round: int):
    SERVER_ROUND.set(server_round)
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
    config = ServerConfig(num_rounds=1)




    return ServerAppComponents(strategy=strategy, config=config)

# ===========================================================
# Create the Flower ServerApp
# ===========================================================
app = ServerApp(server_fn=server_fn)
