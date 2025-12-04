# ...existing code...
"""
FL Analytics Module - Generates human-readable explanations and analytics
for Federated Learning training rounds and sessions.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timezone


class FLAnalytics:
    """Generate analytics and explanations for FL training."""

    def __init__(self):
        self.session_start_time = datetime.now(timezone.utc)
        self.round_history: List[Dict] = []
        self.client_history: Dict[str, List[Dict]] = {}

    def analyze_round(
        self,
        round_num: int,
        central_r2: float,
        central_loss: float,
        client_metrics: Dict[str, Dict],
        aggregated_metrics: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Analyze a training round and generate explanations.

        Note: parameter names are kept for compatibility. `central_r2` is treated
        as central ACCURACY (0..1) to match client_app metrics.
        """
        analysis = {
            "round": round_num,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "round_summary": "",
            "model_status": "",
            "convergence_analysis": "",
            "client_analysis": {},
            "recommendations": "",
            "overall_health": ""
        }

        # Treat central_r2 as central_accuracy to match client metrics
        central_acc = float(central_r2)
        central_loss = float(central_loss)

        # Determine model quality based on accuracy
        acc_quality = self._classify_r2(central_acc)
        loss_trend = self._analyze_loss_trend(central_loss)

        # Generate round summary
        analysis["round_summary"] = self._generate_round_summary(
            round_num, central_acc, central_loss, acc_quality
        )

        # Analyze model status
        analysis["model_status"] = self._generate_model_status(
            central_acc, central_loss, acc_quality
        )

        # Analyze convergence
        analysis["convergence_analysis"] = self._analyze_convergence(
            round_num, central_acc, central_loss
        )

        # Analyze each client (adapted to accuracy/recall keys)
        for client_id, metrics in client_metrics.items():
            analysis["client_analysis"][client_id] = self._analyze_client(
                client_id, metrics, round_num
            )

        # Generate recommendations
        analysis["recommendations"] = self._generate_recommendations(
            round_num, central_acc, central_loss, client_metrics, acc_quality
        )

        # Overall health score
        analysis["overall_health"] = self._calculate_health(
            central_acc, central_loss, client_metrics
        )

        # Store in history (store accuracy as "r2" for backward compatibility)
        self.round_history.append({
            "round": round_num,
            "r2": central_acc,
            "loss": central_loss
        })

        return analysis

    def _classify_r2(self, r2: float) -> str:
        """Classify accuracy quality (keeps name for compatibility)."""
        # r2 here is actually accuracy (0..1)
        if r2 >= 0.95:
            return "excellent"
        elif r2 >= 0.85:
            return "good"
        elif r2 >= 0.70:
            return "moderate"
        elif r2 >= 0.50:
            return "fair"
        else:
            return "poor"

    def _analyze_loss_trend(self, current_loss: float) -> str:
        """Analyze loss trend compared to previous rounds."""
        if len(self.round_history) < 1:
            return "initial"

        prev_loss = self.round_history[-1]["loss"]
        if current_loss < prev_loss * 0.9:
            return "improving_fast"
        elif current_loss < prev_loss:
            return "improving"
        elif current_loss > prev_loss * 1.1:
            return "degrading"
        else:
            return "stable"

    def _generate_round_summary(
        self, round_num: int, r2: float, loss: float, quality: str
    ) -> str:
        """Generate a human-readable round summary using accuracy and loss."""

        quality_descriptions = {
            "excellent": f"Round {round_num}: EXCELLENT accuracy! Model accuracy {r2*100:.1f}%.",
            "good": f"Round {round_num}: Good accuracy. Model accuracy {r2*100:.1f}%.",
            "moderate": f"Round {round_num}: Moderate accuracy at {r2*100:.1f}%.",
            "fair": f"Round {round_num}: Fair accuracy ({r2*100:.1f}%). Consider more data or tuning.",
            "poor": f"Round {round_num}: Poor accuracy ({r2*100:.1f}%). Model needs more training."
        }

        summary = quality_descriptions.get(quality, f"Round {round_num} completed.")

        # Add trend analysis if we have history
        if len(self.round_history) > 0:
            prev_r2 = self.round_history[-1]["r2"]
            r2_change = (r2 - prev_r2) * 100

            if r2_change > 1:
                summary += f" Accuracy improved by {r2_change:.2f} percentage points."
            elif r2_change < -1:
                summary += f" Accuracy decreased by {abs(r2_change):.2f} percentage points."
            else:
                summary += " Accuracy remained stable."

        # Add loss note
        summary += f" Loss: {loss:.6f}."

        return summary

    def _generate_model_status(
        self, r2: float, loss: float, quality: str
    ) -> str:
        """Generate model status explanation using accuracy/recall perspective."""

        status_parts = []

        # Accuracy interpretation
        if r2 >= 0.90:
            status_parts.append(f"The model shows high accuracy ({r2:.4f}).")
        elif r2 >= 0.70:
            status_parts.append(f"The model has acceptable accuracy ({r2:.4f}).")
        else:
            status_parts.append(f"Low accuracy ({r2:.4f}); consider more training or data collection.")

        # Loss interpretation
        if loss < 0.001:
            status_parts.append(f"Loss is very low ({loss:.6f}).")
        elif loss < 0.01:
            status_parts.append(f"Loss is acceptable ({loss:.6f}).")
        else:
            status_parts.append(f"Loss remains high ({loss:.6f}).")

        return " ".join(status_parts)

    def _analyze_convergence(
        self, round_num: int, r2: float, loss: float
    ) -> str:
        """Analyze model convergence using recent accuracy history."""

        if len(self.round_history) < 2:
            return "Insufficient data for convergence analysis. Need at least 3 rounds."

        # Use up to last 3 stored accuracies plus current
        recent = [h["r2"] for h in self.round_history[-3:]] + [r2]
        improvements = [recent[i+1] - recent[i] for i in range(len(recent)-1)]
        avg_improvement = sum(improvements) / len(improvements)

        # Convert to percentage points for messaging
        avg_pct = avg_improvement * 100

        if avg_improvement < 0.0001:
            return "Model has CONVERGED. Accuracy improvements are minimal (<0.01%)."
        elif avg_improvement < 0.001:
            return f"Model is NEAR CONVERGENCE. Accuracy improving slowly ({avg_pct:.3f}% per round)."
        elif avg_improvement > 0.01:
            return f"Model is LEARNING FAST. Accuracy improving by {avg_pct:.2f}% per round."
        else:
            return f"Model is LEARNING STEADILY. Accuracy improving by {avg_pct:.3f}% per round."

    def _analyze_client(
        self, client_id: str, metrics: Dict, round_num: int
    ) -> str:
        """Analyze individual client performance (accuracy & recall aware)."""

        parts = [f"Client {client_id}:"]

        # Training accuracy
        if "train_accuracy" in metrics:
            train_acc = float(metrics["train_accuracy"])
            if train_acc >= 0.90:
                parts.append(f"Train Acc={train_acc:.4f} (excellent)")
            elif train_acc >= 0.70:
                parts.append(f"Train Acc={train_acc:.4f} (good)")
            else:
                parts.append(f"Train Acc={train_acc:.4f} (needs improvement)")

        # Test accuracy
        if "test_accuracy" in metrics:
            test_acc = float(metrics["test_accuracy"])
            parts.append(f"Test Acc={test_acc:.4f}")

            # Overfitting check
            if "train_accuracy" in metrics:
                if float(metrics["train_accuracy"]) - test_acc > 0.1:
                    parts.append("⚠️ Possible overfitting detected")

        # Recall checks (train/test)
        if "train_recall" in metrics:
            parts.append(f"Train Recall={float(metrics['train_recall']):.3f}")
        if "test_recall" in metrics:
            parts.append(f"Test Recall={float(metrics['test_recall']):.3f}")

        # F1 if present
        if "train_f1" in metrics:
            parts.append(f"Train F1={float(metrics['train_f1']):.3f}")
        if "test_f1" in metrics:
            parts.append(f"Test F1={float(metrics['test_f1']):.3f}")

        # Resource usage (fit stage keys)
        if "cpu_percent_fit" in metrics:
            cpu = metrics["cpu_percent_fit"]
            if cpu > 80:
                parts.append(f"CPU usage high ({cpu:.1f}%)")
        if "memory_mb_fit" in metrics:
            mem = metrics["memory_mb_fit"]