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
        central_accuracy: float,
        central_loss: float,
        central_recall: Optional[float],
        client_metrics: Dict[str, Dict],
        aggregated_metrics: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Analyze a training round and generate explanations.

        Note: parameter names are kept for compatibility. `central_accuracy` is treated
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

        # Treat central_accuracy as central_accuracy to match client metrics
        central_acc = float(central_accuracy)
        central_loss = float(central_loss)
        # Central recall (optional)
        central_rec = float(central_recall) if central_recall is not None else None

        # Determine model quality based on accuracy
        acc_quality = self._classify_accuracy(central_accuracy)
        loss_trend = self._analyze_loss_trend(central_loss)

        # Generate round summary
        analysis["round_summary"] = self._generate_round_summary(
            round_num, central_acc, central_loss, acc_quality
        )

        # Generate recall-specific section (mirrors accuracy logic)
        if central_rec is not None:
            rec_quality = self._classify_recall(central_rec)
            analysis["recall_section"] = {
                "recall": central_rec,
                "recall_quality": rec_quality,
                "recall_summary": self._generate_recall_summary(round_num, central_rec, central_loss, rec_quality),
                "recall_status": self._generate_recall_status(central_rec, central_loss, rec_quality),
                "recall_convergence": self._analyze_recall_convergence(round_num, central_rec, central_loss)
            }
        else:
            analysis["recall_section"] = None

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

        # Store in history (store accuracy as "accuracy" for backward compatibility)
        self.round_history.append({
            "round": round_num,
            "accuracy": central_accuracy,
            "loss": central_loss,
            "recall": central_recall
        })

        return analysis

    def _classify_accuracy(self, accuracy: float) -> str:
        """Classify accuracy quality (keeps name for compatibility)."""
        # accuracy here is actually accuracy (0..1)
        if accuracy >= 0.95:
            return "excellent"
        elif accuracy >= 0.85:
            return "good"
        elif accuracy >= 0.70:
            return "moderate"
        elif accuracy >= 0.50:
            return "fair"
        else:
            return "poor"

    # --- Recall helpers (mirror accuracy helpers) ---
    def _classify_recall(self, recall: float) -> str:
        """Classify recall quality by reusing accuracy thresholds."""
        return self._classify_accuracy(recall)

    def _generate_recall_summary(
        self, round_num: int, recall: float, loss: float, quality: str
    ) -> str:
        """Generate a recall-oriented round summary. Mirrors accuracy summary."""
        # Reuse the round summary logic but feed recall in place of accuracy so wording
        # stays consistent with accuracy summaries.
        return self._generate_round_summary(round_num, recall, loss, quality)

    def _generate_recall_status(self, recall: float, loss: float, quality: str) -> str:
        """Generate model status text for recall (mirrors accuracy status)."""
        return self._generate_model_status(recall, loss, quality)

    def _analyze_recall_convergence(
        self, round_num: int, recall: float, loss: float
    ) -> str:
        """Analyze convergence using recent recall history (mirrors accuracy convergence)."""

        if len(self.round_history) < 2:
            return "Insufficient data for recall convergence analysis. Need at least 3 rounds."

        # Use up to last 3 stored recalls plus current
        recent = [h.get("recall", 0) for h in self.round_history[-3:]] + [recall]
        improvements = [recent[i+1] - recent[i] for i in range(len(recent)-1)]
        avg_improvement = sum(improvements) / len(improvements)

        # Convert to percentage points for messaging
        avg_pct = avg_improvement * 100

        if avg_improvement < 0.0001:
            return "Recall has CONVERGED. Improvements are minimal (<0.01%)."
        elif avg_improvement < 0.001:
            return f"Recall is NEAR CONVERGENCE. Improving slowly ({avg_pct:.3f}% per round)."
        elif avg_improvement > 0.01:
            return f"Recall is IMPROVING FAST. Improving by {avg_pct:.2f}% per round."
        else:
            return f"Recall is IMPROVING STEADILY. Improving by {avg_pct:.3f}% per round."

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
        self, round_num: int, accuracy: float, loss: float, quality: str
    ) -> str:
        """Generate a human-readable round summary using accuracy and loss."""

        quality_descriptions = {
            "excellent": f"Round {round_num}: EXCELLENT accuracy! Model accuracy {accuracy*100:.1f}%.",
            "good": f"Round {round_num}: Good accuracy. Model accuracy {accuracy*100:.1f}%.",
            "moderate": f"Round {round_num}: Moderate accuracy at {accuracy*100:.1f}%.",
            "fair": f"Round {round_num}: Fair accuracy ({accuracy*100:.1f}%). Consider more data or tuning.",
            "poor": f"Round {round_num}: Poor accuracy ({accuracy*100:.1f}%). Model needs more training."
        }

        summary = quality_descriptions.get(quality, f"Round {round_num} completed.")

        # Add trend analysis if we have history
        if len(self.round_history) > 0:
            prev_accuracy = self.round_history[-1]["accuracy"]
            accuracy_change = (accuracy - accuracy) * 100

            if accuracy_change > 1:
                summary += f" Accuracy improved by {accuracy_change:.2f} percentage points."
            elif accuracy_change < -1:
                summary += f" Accuracy decreased by {abs(accuracy_change):.2f} percentage points."
            else:
                summary += " Accuracy remained stable."

        # Add loss note
        summary += f" Loss: {loss:.6f}."

        return summary

    def _generate_model_status(
        self, accuracy: float, loss: float, quality: str
    ) -> str:
        """Generate model status explanation using accuracy/recall perspective."""

        status_parts = []

        # Accuracy interpretation
        if accuracy >= 0.90:
            status_parts.append(f"The model shows high accuracy ({accuracy:.4f}).")
        elif accuracy >= 0.70:
            status_parts.append(f"The model has acceptable accuracy ({accuracy:.4f}).")
        else:
            status_parts.append(f"Low accuracy ({accuracy:.4f}); consider more training or data collection.")

        # Loss interpretation
        if loss < 0.001:
            status_parts.append(f"Loss is very low ({loss:.6f}).")
        elif loss < 0.01:
            status_parts.append(f"Loss is acceptable ({loss:.6f}).")
        else:
            status_parts.append(f"Loss remains high ({loss:.6f}).")

        return " ".join(status_parts)

    def _analyze_convergence(
        self, round_num: int, accuracy: float, loss: float
    ) -> str:
        """Analyze model convergence using recent accuracy history."""

        if len(self.round_history) < 2:
            return "Insufficient data for convergence analysis. Need at least 3 rounds."

        # Use up to last 3 stored accuracies plus current
        recent = [h["accuracy"] for h in self.round_history[-3:]] + [accuracy]
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

    def _generate_recommendations(
        self, round_num: int, accuracy: float, loss: float,
        client_metrics: Dict[str, Dict], quality: str
    ) -> str:
        """Generate recommendations based on current state."""

        recommendations = []

        # Based on overall quality
        if quality == "excellent":
            recommendations.append("✅ Model is performing excellently. Consider saving this model checkpoint.")
        elif quality == "good":
            recommendations.append("👍 Good progress. Continue training for potential improvements.")
        elif quality == "poor":
            recommendations.append("⚠️ Consider adjusting learning rate or increasing local epochs.")

        # Based on convergence
        if len(self.round_history) >= 3:
            recent_accuracys = [h["accuracy"] for h in self.round_history[-3:]]
            if max(recent_accuracys) - min(recent_accuracys) < 0.001:
                recommendations.append("📊 Model appears converged. Training can be stopped.")

        # Based on client variance
        if client_metrics:
            accuracy_values = []
            for m in client_metrics.values():
                if "train_accuracy" in m:
                    accuracy_values.append(m["train_accuracy"])

            if accuracy_values:
                variance = max(accuracy_values) - min(accuracy_values)
                if variance > 0.1:
                    recommendations.append(f"⚖️ High variance ({variance:.2f}) between clients. Data may be non-IID.")

        # Round-based recommendation
        if round_num == 1:
            recommendations.append("🚀 First round complete. Initial model established.")
        elif round_num >= 10:
            if accuracy < 0.70:
                recommendations.append("💡 After 10 rounds with R²<0.70, consider model architecture changes.")

        return " | ".join(recommendations) if recommendations else "Continue training."

    def _calculate_health(
        self, accuracy: float, loss: float, client_metrics: Dict[str, Dict]
    ) -> str:
        """Calculate overall training health score."""

        # Score components (0-100 each)
        accuracy_score = min(accuracy * 100, 100)

        # Loss score (inverse, lower is better)
        if loss < 0.001:
            loss_score = 100
        elif loss < 0.01:
            loss_score = 80
        elif loss < 0.1:
            loss_score = 60
        else:
            loss_score = 40

        # Client consistency score
        if client_metrics:
            accuracy_values = [m.get("train_accuracy", 0) for m in client_metrics.values()]
            if accuracy_values:
                consistency = 1 - (max(accuracy_values) - min(accuracy_values))
                consistency_score = consistency * 100
            else:
                consistency_score = 50
        else:
            consistency_score = 50

        # Overall score
        overall = (accuracy_score * 0.5) + (loss_score * 0.3) + (consistency_score * 0.2)

        if overall >= 90:
            return f"🟢 HEALTHY ({overall:.0f}/100)"
        elif overall >= 70:
            return f"🟡 GOOD ({overall:.0f}/100)"
        elif overall >= 50:
            return f"🟠 MODERATE ({overall:.0f}/100)"
        else:
            return f"🔴 NEEDS ATTENTION ({overall:.0f}/100)"

    def generate_session_summary(
        self, total_rounds: int, final_accuracy: float, final_loss: float
    ) -> str:
        """Generate end-of-session summary."""

        summary_parts = [
            f"═══════════════════════════════════════",
            f"FL TRAINING SESSION COMPLETE",
            f"═══════════════════════════════════════",
            f"Total Rounds: {total_rounds}",
            f"Final R²: {final_accuracy:.4f} ({self._classify_accuracy(final_accuracy).upper()})",
            f"Final Loss: {final_loss:.6f}",
        ]

        if len(self.round_history) > 1:
            initial_accuracy = self.round_history[0]["accuracy"]
            accuracy_improvement = final_accuracy - initial_accuracy
            summary_parts.append(f"R² Improvement: {accuracy_improvement*100:.2f}%")

            initial_loss = self.round_history[0]["loss"]
            loss_reduction = ((initial_loss - final_loss) / initial_loss) * 100
            summary_parts.append(f"Loss Reduction: {loss_reduction:.1f}%")

        # Client summary
        if self.client_history:
            summary_parts.append(f"Clients Participated: {len(self.client_history)}")

        summary_parts.append(f"═══════════════════════════════════════")

        return "\n".join(summary_parts)


# Global analytics instance
_analytics: Optional[FLAnalytics] = None


def get_analytics() -> FLAnalytics:
    """Get or create the global analytics instance."""
    global _analytics
    if _analytics is None:
        _analytics = FLAnalytics()
    return _analytics


def reset_analytics():
    """Reset analytics for a new session."""
    global _analytics
    _analytics = FLAnalytics()