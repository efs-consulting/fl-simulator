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
    - Per-round metrics (aggregated R², loss)
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
        """
        Initialize the FL experiment tracker.

        Args:
            experiment_name: Name of the MLflow experiment
            tracking_uri: MLflow tracking server URI (default: local ./mlruns)
            artifact_location: Where to store artifacts
        """
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
            # Default to local tracking
            mlflow.set_tracking_uri("file:./mlruns")

        # Set or create experiment
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
        """
        Start a new MLflow run for an FL training session.

        Args:
            run_name: Optional name for the run
            tags: Optional tags to add to the run

        Returns:
            Run ID if successful, None otherwise
        """
        if not self.enabled:
            return None

        if run_name is None:
            run_name = f"FL-Run-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        # Start MLflow run
        run = mlflow.start_run(run_name=run_name)
        self.run_id = run.info.run_id

        # Add default tags
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
        """
        Log FL configuration parameters.

        Args:
            num_rounds: Number of FL rounds
            min_clients: Minimum clients per round
            penalty: Regularization type
            local_epochs: Local training epochs per round
            learning_rate: Learning rate
            **extra_params: Additional parameters to log
        """
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
        aggregated_train_r2: float,
        aggregated_test_r2: Optional[float] = None,
        aggregated_loss: Optional[float] = None,
        central_eval_r2: Optional[float] = None,
        central_eval_loss: Optional[float] = None,
        num_clients: int = 0,
        duration_sec: Optional[float] = None
    ):
        """
        Log metrics for a completed FL round.

        Args:
            round_num: Current round number
            aggregated_train_r2: Weighted average training R²
            aggregated_test_r2: Weighted average test R²
            aggregated_loss: Weighted average loss
            central_eval_r2: Central evaluation R²
            central_eval_loss: Central evaluation loss
            num_clients: Number of participating clients
            duration_sec: Round duration in seconds
        """
        if not self.enabled:
            return

        metrics = {
            "round": round_num,
            "aggregated_train_r2": aggregated_train_r2,
        }

        if aggregated_test_r2 is not None:
            metrics["aggregated_test_r2"] = aggregated_test_r2
        if aggregated_loss is not None:
            metrics["aggregated_loss"] = aggregated_loss
        if central_eval_r2 is not None:
            metrics["central_eval_r2"] = central_eval_r2
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

        # Store locally for summary
        self.round_metrics.append(metrics)

    def log_client_metrics(
        self,
        client_id: str,
        round_num: int,
        train_r2: float,
        test_r2: Optional[float] = None,
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
            train_r2: Client's training R²
            test_r2: Client's test R²
            loss: Client's loss
            cpu_percent: CPU usage during training
            memory_mb: Memory usage in MB
            samples: Number of training samples
        """
        if not self.enabled:
            return

        metrics = {
            "round": round_num,
            "train_r2": train_r2,
        }

        if test_r2 is not None:
            metrics["test_r2"] = test_r2
        if loss is not None:
            metrics["loss"] = loss
        if cpu_percent is not None:
            metrics["cpu_percent"] = cpu_percent
        if memory_mb is not None:
            metrics["memory_mb"] = memory_mb
        if samples is not None:
            metrics["samples"] = samples

        # Log with client-specific metric names
        for key, value in metrics.items():
            if key != "round":
                mlflow.log_metric(f"client_{client_id}_{key}", value, step=round_num)

        # Store locally
        if client_id not in self.client_metrics:
            self.client_metrics[client_id] = []
        self.client_metrics[client_id].append(metrics)

    def log_model_artifact(
        self,
        model_path: str,
        artifact_name: str = "final_model"
    ):
        """
        Log model weights as an artifact.

        Args:
            model_path: Path to the model file (.npz)
            artifact_name: Name for the artifact
        """
        if not self.enabled:
            return

        if os.path.exists(model_path):
            mlflow.log_artifact(model_path, artifact_name)
            print(f"Model artifact logged: {model_path}")
        else:
            print(f"Model file not found: {model_path}")

    def log_training_summary(self):
        """
        Log a summary of the training session.
        """
        if not self.enabled or not self.round_metrics:
            return

        # Calculate summary statistics
        train_r2_values = [m["aggregated_train_r2"] for m in self.round_metrics]

        summary = {
            "total_rounds": len(self.round_metrics),
            "final_train_r2": train_r2_values[-1],
            "best_train_r2": max(train_r2_values),
            "avg_train_r2": np.mean(train_r2_values),
            "total_clients": len(self.client_metrics),
        }

        # Log loss if available
        loss_values = [m.get("aggregated_loss") for m in self.round_metrics if m.get("aggregated_loss")]
        if loss_values:
            summary["final_loss"] = loss_values[-1]
            summary["best_loss"] = min(loss_values)
            summary["avg_loss"] = np.mean(loss_values)

        # Log central eval if available
        central_r2_values = [m.get("central_eval_r2") for m in self.round_metrics if m.get("central_eval_r2")]
        if central_r2_values:
            summary["final_central_r2"] = central_r2_values[-1]
            summary["best_central_r2"] = max(central_r2_values)

        for key, value in summary.items():
            mlflow.log_metric(f"summary_{key}", value)

        # Save detailed metrics as JSON artifact
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
        """
        End the current MLflow run.

        Args:
            status: Run status (FINISHED, FAILED, KILLED)
        """
        if not self.enabled:
            return

        # Log final summary
        self.log_training_summary()

        # End the run
        mlflow.end_run(status=status)
        print(f"MLflow run ended: {self.run_id} ({status})")

        # Reset state
        self.run_id = None
        self.round_metrics = []
        self.client_metrics = {}


# Singleton instance for easy access
_tracker: Optional[FLExperimentTracker] = None


def get_tracker(
    experiment_name: str = "FL-Battery-SOH",
    **kwargs
) -> FLExperimentTracker:
    """
    Get or create the global FL experiment tracker.

    Args:
        experiment_name: Name of the MLflow experiment
        **kwargs: Additional arguments for FLExperimentTracker

    Returns:
        FLExperimentTracker instance
    """
    global _tracker
    if _tracker is None:
        _tracker = FLExperimentTracker(experiment_name, **kwargs)
    return _tracker


# Example integration with server_app.py:
"""
# In server_app.py, add:

from sklearnexample.mlflow_tracking import get_tracker

# In server_fn():
tracker = get_tracker()
tracker.start_run(run_name=f"FL-{num_rounds}rounds-{min_clients}clients")
tracker.log_fl_config(
    num_rounds=num_rounds,
    min_clients=min_clients,
    penalty=penalty,
    local_epochs=5
)

# In weighted_average():
tracker.log_round_metrics(
    round_num=server_round,
    aggregated_train_r2=aggregated["train_r_squared"],
    aggregated_loss=aggregated.get("loss"),
    num_clients=len(metrics)
)

# For each client in metrics:
tracker.log_client_metrics(
    client_id=cid,
    round_num=server_round,
    train_r2=client_metrics["train_r_squared"],
    loss=client_metrics.get("loss")
)

# At end of training:
tracker.log_model_artifact("/app/model/final_model.npz")
tracker.end_run()
"""
