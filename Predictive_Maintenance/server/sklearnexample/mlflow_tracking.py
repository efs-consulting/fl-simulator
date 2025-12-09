"""
MLflow Integration for FL Simulator Experiment Tracking
Created: 2025-11-29

This module provides MLflow integration for tracking FL experiments,
including model parameters, metrics, and artifacts.
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
import numpy as np

# MLflow import with fallback
try:
    import mlflow
    from mlflow.tracking import MlflowClient
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False
    print("MLflow not installed. Run: pip install mlflow")


class FLExperimentTracker:
    """
    MLflow-based experiment tracker for Federated Learning.

    Tracks:
    - FL hyperparameters (rounds, clients, strategy)
    - Per-round metrics (aggregated accuracy, recall, loss)
    - Per-client metrics
    - Model artifacts (final weights)
    - Training duration and resource usage
    """

    def __init__(
        self,
        experiment_name: str = "FL-Battery-SOH",
        tracking_uri: Optional[str] = None,
        artifact_location: Optional[str] = None
    ):
        self.experiment_name = experiment_name
        self.enabled = MLFLOW_AVAILABLE and not os.getenv("DISABLE_MLFLOW")

        if not self.enabled:
            print("MLflow tracking disabled")
            return

        # Configure MLflow
        if tracking_uri:
            mlflow.set_tracking_uri(tracking_uri)
        elif os.getenv("MLFLOW_TRACKING_URI"):
            mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI"))
        else:
            mlflow.set_tracking_uri("file:./mlruns")

        mlflow.set_experiment(experiment_name)
        self.client = MlflowClient()

        self.run_id = None
        self.round_metrics: List[Dict] = []
        self.client_metrics: Dict[str, List[Dict]] = {}

    def start_run(
        self,
        run_name: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> Optional[str]:
        if not self.enabled:
            return None

        if run_name is None:
            run_name = f"FL-Run-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        run = mlflow.start_run(run_name=run_name)
        self.run_id = run.info.run_id

        default_tags = {
            "framework": "flower",
            "task": "battery-soh-prediction",
            "model_type": "sgd_regressor",
            "timestamp": datetime.now().isoformat()
        }
        if tags:
            default_tags.update(tags)

        mlflow.set_tags(default_tags)

        print(f"MLflow run started: {self.run_id}")
        return self.run_id

    def log_fl_config(
        self,
        num_rounds: int,
        min_clients: int,
        penalty: str = "l2",
        local_epochs: int = 5,
        learning_rate: float = 1e-5,
        **extra_params
    ):
        if not self.enabled:
            return

        params = {
            "fl_num_rounds": num_rounds,
            "fl_min_clients": min_clients,
            "fl_strategy": "FedAvg",
            "model_penalty": penalty,
            "local_epochs": local_epochs,
            "learning_rate": learning_rate,
        }
        params.update(extra_params)

        mlflow.log_params(params)

    def log_round_metrics(
        self,
        round_num: int,
        aggregated_train_accuracy: float,
        aggregated_train_recall: Optional[float] = None,
        aggregated_train_f1: Optional[float] = None,
        aggregated_test_accuracy: Optional[float] = None,
        aggregated_test_recall: Optional[float] = None,
        aggregated_test_f1: Optional[float] = None,
        aggregated_loss: Optional[float] = None,
        central_eval_accuracy: Optional[float] = None,
        central_eval_recall: Optional[float] = None,
        central_eval_loss: Optional[float] = None,
        num_clients: int = 0,
        duration_sec: Optional[float] = None
    ):
        """
        Log metrics for a completed FL round.

        Args:
            round_num: Current round number
            aggregated_train_accuracy: Weighted average training accuracy
            aggregated_train_recall: Weighted average training recall
            aggregated_train_f1: Weighted average training F1
            aggregated_test_accuracy: Weighted average test accuracy
            aggregated_test_recall: Weighted average test recall
            aggregated_test_f1: Weighted average test F1
            aggregated_loss: Weighted average loss
            central_eval_accuracy: Central evaluation accuracy
            central_eval_recall: Central evaluation recall
            central_eval_loss: Central evaluation loss
            num_clients: Number of participating clients
            duration_sec: Round duration in seconds
        """
        if not self.enabled:
            return

        metrics = {
            "round": round_num,
            "aggregated_train_accuracy": aggregated_train_accuracy,
        }

        if aggregated_train_recall is not None:
            metrics["aggregated_train_recall"] = aggregated_train_recall
        if aggregated_train_f1 is not None:
            metrics["aggregated_train_f1"] = aggregated_train_f1
        if aggregated_test_accuracy is not None:
            metrics["aggregated_test_accuracy"] = aggregated_test_accuracy
        if aggregated_test_recall is not None:
            metrics["aggregated_test_recall"] = aggregated_test_recall
        if aggregated_test_f1 is not None:
            metrics["aggregated_test_f1"] = aggregated_test_f1
        if aggregated_loss is not None:
            metrics["aggregated_loss"] = aggregated_loss
        if central_eval_accuracy is not None:
            metrics["central_eval_accuracy"] = central_eval_accuracy
        if central_eval_recall is not None:
            metrics["central_eval_recall"] = central_eval_recall
        if central_eval_loss is not None:
            metrics["central_eval_loss"] = central_eval_loss
        if num_clients > 0:
            metrics["num_clients"] = num_clients
        if duration_sec is not None:
            metrics["round_duration_sec"] = duration_sec

        # Log to MLflow with step = round_num
        for key, value in metrics.items():
            if key != "round":
                mlflow.log_metric(key, value, step=round_num)

        self.round_metrics.append(metrics)

    def log_client_metrics(
        self,
        client_id: str,
        round_num: int,
        train_accuracy: float,
        train_recall: Optional[float] = None,
        train_f1: Optional[float] = None,
        test_accuracy: Optional[float] = None,
        test_recall: Optional[float] = None,
        test_f1: Optional[float] = None,
        loss: Optional[float] = None,
        cpu_percent: Optional[float] = None,
        memory_mb: Optional[float] = None,
        samples: Optional[int] = None
    ):
        """
        Log metrics for a specific client in a round.

        Args:
            client_id: Client identifier
            round_num: Current round number
            train_accuracy: Client's training accuracy
            train_recall: Client's training recall
            train_f1: Client's training F1
            test_accuracy: Client's test accuracy
            test_recall: Client's test recall
            test_f1: Client's test F1
            loss: Client's loss
            cpu_percent: CPU usage during training
            memory_mb: Memory usage in MB
            samples: Number of training samples
        """
        if not self.enabled:
            return

        metrics = {
            "round": round_num,
            "train_accuracy": train_accuracy,
        }

        if train_recall is not None:
            metrics["train_recall"] = train_recall
        if train_f1 is not None:
            metrics["train_f1"] = train_f1
        if test_accuracy is not None:
            metrics["test_accuracy"] = test_accuracy
        if test_recall is not None:
            metrics["test_recall"] = test_recall
        if test_f1 is not None:
            metrics["test_f1"] = test_f1
        if loss is not None:
            metrics["loss"] = loss
        if cpu_percent is not None:
            metrics["cpu_percent"] = cpu_percent
        if memory_mb is not None:
            metrics["memory_mb"] = memory_mb
        if samples is not None:
            metrics["samples"] = samples

        for key, value in metrics.items():
            if key != "round":
                mlflow.log_metric(f"client_{client_id}_{key}", value, step=round_num)

        if client_id not in self.client_metrics:
            self.client_metrics[client_id] = []
        self.client_metrics[client_id].append(metrics)

    def log_model_artifact(
        self,
        model_path: str,
        artifact_name: str = "final_model"
    ):
        if not self.enabled:
            return

        if os.path.exists(model_path):
            mlflow.log_artifact(model_path, artifact_name)
            print(f"Model artifact logged: {model_path}")
        else:
            print(f"Model file not found: {model_path}")

    def log_training_summary(self):
        if not self.enabled or not self.round_metrics:
            return

        train_acc_values = [m["aggregated_train_accuracy"] for m in self.round_metrics if "aggregated_train_accuracy" in m]
        train_rec_values = [m.get("aggregated_train_recall") for m in self.round_metrics if m.get("aggregated_train_recall") is not None]

        summary = {
            "total_rounds": len(self.round_metrics),
            "final_train_accuracy": train_acc_values[-1] if train_acc_values else None,
            "best_train_accuracy": max(train_acc_values) if train_acc_values else None,
            "avg_train_accuracy": np.mean(train_acc_values) if train_acc_values else None,
            "final_train_recall": train_rec_values[-1] if train_rec_values else None,
            "best_train_recall": max(train_rec_values) if train_rec_values else None,
            "avg_train_recall": np.mean(train_rec_values) if train_rec_values else None,
            "total_clients": len(self.client_metrics),
        }

        loss_values = [m.get("aggregated_loss") for m in self.round_metrics if m.get("aggregated_loss") is not None]
        if loss_values:
            summary["final_loss"] = loss_values[-1]
            summary["best_loss"] = min(loss_values)
            summary["avg_loss"] = np.mean(loss_values)

        central_acc_values = [m.get("central_eval_accuracy") for m in self.round_metrics if m.get("central_eval_accuracy") is not None]
        if central_acc_values:
            summary["final_central_accuracy"] = central_acc_values[-1]
            summary["best_central_accuracy"] = max(central_acc_values)

        central_rec_values = [m.get("central_eval_recall") for m in self.round_metrics if m.get("central_eval_recall") is not None]
        if central_rec_values:
            summary["final_central_recall"] = central_rec_values[-1]
            summary["best_central_recall"] = max(central_rec_values)

        for key, value in summary.items():
            mlflow.log_metric(f"summary_{key}", value)

        metrics_summary = {
            "round_metrics": self.round_metrics,
            "client_metrics": self.client_metrics,
            "summary": summary
        }

        summary_path = "/tmp/fl_metrics_summary.json"
        with open(summary_path, "w") as f:
            json.dump(metrics_summary, f, indent=2, default=str)
        mlflow.log_artifact(summary_path, "metrics")

        print(f"Training summary logged: {summary}")

    def end_run(self, status: str = "FINISHED"):
        if not self.enabled:
            return

        self.log_training_summary()
        mlflow.end_run(status=status)
        print(f"MLflow run ended: {self.run_id} ({status})")

        self.run_id = None
        self.round_metrics = []
        self.client_metrics = {}


# Singleton instance for easy access
_tracker: Optional[FLExperimentTracker] = None


def get_tracker(
    experiment_name: str = "FL-Battery-SOH",
    **kwargs
) -> FLExperimentTracker:
    global _tracker
    if _tracker is None:
        _tracker = FLExperimentTracker(experiment_name, **kwargs)
    return _tracker

# Example integration with server_app.py:
"""
from sklearnexample.mlflow_tracking import get_tracker

tracker = get_tracker()
tracker.start_run(run_name=f"FL-{num_rounds}rounds-{min_clients}clients")
tracker.log_fl_config(
    num_rounds=num_rounds,
    min_clients=min_clients,
    penalty=penalty,
    local_epochs=5
)

tracker.log_round_metrics(
    round_num=server_round,
    aggregated_train_accuracy=aggregated["train_accuracy"],
    aggregated_train_recall=aggregated.get("train_recall"),
    aggregated_train_f1=aggregated.get("train_f1"),
    aggregated_test_accuracy=aggregated.get("test_accuracy"),
    aggregated_test_recall=aggregated.get("test_recall"),
    aggregated_test_f1=aggregated.get("test_f1"),
    aggregated_loss=aggregated.get("loss"),
    central_eval_accuracy=metrics.get("accuracy"),
    central_eval_recall=metrics.get("recall"),
    central_eval_loss=metrics.get("loss"),
    num_clients=len(metrics)
)

tracker.log_client_metrics(
    client_id=cid,
    round_num=server_round,
    train_accuracy=client_metrics["train_accuracy"],
    train_recall=client_metrics.get("train_recall"),
    train_f1=client_metrics.get("train_f1"),
    test_accuracy=client_metrics.get("test_accuracy"),
    test_recall=client_metrics.get("test_recall"),
    test_f1=client_metrics.get("test_f1"),
    loss=client_metrics.get("loss")
)

tracker.log_model_artifact("/app/model/final_model.npz")
tracker.end_run()
"""