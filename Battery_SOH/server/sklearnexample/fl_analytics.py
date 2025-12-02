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

        Returns:
            Dict with 'round_summary', 'client_analysis', 'recommendations'
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

        # Determine model quality based on R²
        r2_quality = self._classify_r2(central_r2)
        loss_trend = self._analyze_loss_trend(central_loss)

        # Generate round summary
        analysis["round_summary"] = self._generate_round_summary(
            round_num, central_r2, central_loss, r2_quality
        )

        # Analyze model status
        analysis["model_status"] = self._generate_model_status(
            central_r2, central_loss, r2_quality
        )

        # Analyze convergence
        analysis["convergence_analysis"] = self._analyze_convergence(
            round_num, central_r2, central_loss
        )

        # Analyze each client
        for client_id, metrics in client_metrics.items():
            analysis["client_analysis"][client_id] = self._analyze_client(
                client_id, metrics, round_num
            )

        # Generate recommendations
        analysis["recommendations"] = self._generate_recommendations(
            round_num, central_r2, central_loss, client_metrics, r2_quality
        )

        # Overall health score
        analysis["overall_health"] = self._calculate_health(
            central_r2, central_loss, client_metrics
        )

        # Store in history
        self.round_history.append({
            "round": round_num,
            "r2": central_r2,
            "loss": central_loss
        })

        return analysis

    def _classify_r2(self, r2: float) -> str:
        """Classify R² score quality."""
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
        """Generate a human-readable round summary."""

        quality_descriptions = {
            "excellent": f"Round {round_num}: EXCELLENT performance! Model explains {r2*100:.1f}% of variance.",
            "good": f"Round {round_num}: Good performance. Model explains {r2*100:.1f}% of variance.",
            "moderate": f"Round {round_num}: Moderate performance. Model explains {r2*100:.1f}% of variance.",
            "fair": f"Round {round_num}: Fair performance. Room for improvement with {r2*100:.1f}% variance explained.",
            "poor": f"Round {round_num}: Poor performance. Only {r2*100:.1f}% variance explained. Model needs more training."
        }

        summary = quality_descriptions.get(quality, f"Round {round_num} completed.")

        # Add trend analysis if we have history
        if len(self.round_history) > 0:
            prev_r2 = self.round_history[-1]["r2"]
            r2_change = (r2 - prev_r2) * 100

            if r2_change > 1:
                summary += f" R² improved by {r2_change:.2f} percentage points."
            elif r2_change < -1:
                summary += f" R² decreased by {abs(r2_change):.2f} percentage points."
            else:
                summary += " R² remained stable."

        return summary

    def _generate_model_status(
        self, r2: float, loss: float, quality: str
    ) -> str:
        """Generate model status explanation."""

        status_parts = []

        # R² interpretation
        if r2 >= 0.90:
            status_parts.append(f"The model is highly accurate (R²={r2:.4f}), explaining most of the battery SOH variance.")
        elif r2 >= 0.70:
            status_parts.append(f"The model has good predictive power (R²={r2:.4f}) for battery SOH estimation.")
        else:
            status_parts.append(f"The model needs improvement (R²={r2:.4f}). Consider more training rounds or data.")

        # Loss interpretation
        if loss < 0.001:
            status_parts.append(f"Loss is very low ({loss:.6f}), indicating precise predictions.")
        elif loss < 0.01:
            status_parts.append(f"Loss is acceptable ({loss:.6f}).")
        else:
            status_parts.append(f"Loss is still high ({loss:.6f}). More optimization needed.")

        return " ".join(status_parts)

    def _analyze_convergence(
        self, round_num: int, r2: float, loss: float
    ) -> str:
        """Analyze model convergence."""

        if len(self.round_history) < 2:
            return "Insufficient data for convergence analysis. Need at least 3 rounds."

        # Calculate R² improvements over last few rounds
        recent_r2s = [h["r2"] for h in self.round_history[-3:]] + [r2]
        r2_improvements = [recent_r2s[i+1] - recent_r2s[i] for i in range(len(recent_r2s)-1)]
        avg_improvement = sum(r2_improvements) / len(r2_improvements)

        if avg_improvement < 0.0001:
            return f"Model has CONVERGED. R² improvements are minimal (<0.01%). Consider stopping training."
        elif avg_improvement < 0.001:
            return f"Model is NEAR CONVERGENCE. R² improving slowly ({avg_improvement*100:.3f}% per round)."
        elif avg_improvement > 0.01:
            return f"Model is LEARNING FAST. R² improving by {avg_improvement*100:.2f}% per round. Continue training."
        else:
            return f"Model is LEARNING STEADILY. R² improving by {avg_improvement*100:.3f}% per round."

    def _analyze_client(
        self, client_id: str, metrics: Dict, round_num: int
    ) -> str:
        """Analyze individual client performance."""

        parts = [f"Client {client_id}:"]

        # Training performance
        if "train_r2" in metrics:
            train_r2 = metrics["train_r2"]
            if train_r2 >= 0.90:
                parts.append(f"Training R²={train_r2:.4f} (excellent local fit)")
            elif train_r2 >= 0.70:
                parts.append(f"Training R²={train_r2:.4f} (good local fit)")
            else:
                parts.append(f"Training R²={train_r2:.4f} (needs improvement)")

        # Test performance
        if "test_r2" in metrics:
            test_r2 = metrics["test_r2"]
            parts.append(f"Test R²={test_r2:.4f}")

            # Overfitting check
            if "train_r2" in metrics:
                if metrics["train_r2"] - test_r2 > 0.1:
                    parts.append("⚠️ Possible overfitting detected")

        # Resource usage
        if "cpu_percent" in metrics:
            cpu = metrics["cpu_percent"]
            if cpu > 80:
                parts.append(f"CPU usage high ({cpu:.1f}%)")

        if "memory_mb" in metrics:
            mem = metrics["memory_mb"]
            parts.append(f"Memory: {mem:.1f}MB")

        # Store client history
        if client_id not in self.client_history:
            self.client_history[client_id] = []
        self.client_history[client_id].append({
            "round": round_num,
            "metrics": metrics
        })

        return " | ".join(parts)

    def _generate_recommendations(
        self, round_num: int, r2: float, loss: float,
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
            recent_r2s = [h["r2"] for h in self.round_history[-3:]]
            if max(recent_r2s) - min(recent_r2s) < 0.001:
                recommendations.append("📊 Model appears converged. Training can be stopped.")

        # Based on client variance
        if client_metrics:
            r2_values = []
            for m in client_metrics.values():
                if "train_r2" in m:
                    r2_values.append(m["train_r2"])

            if r2_values:
                variance = max(r2_values) - min(r2_values)
                if variance > 0.1:
                    recommendations.append(f"⚖️ High variance ({variance:.2f}) between clients. Data may be non-IID.")

        # Round-based recommendation
        if round_num == 1:
            recommendations.append("🚀 First round complete. Initial model established.")
        elif round_num >= 10:
            if r2 < 0.70:
                recommendations.append("💡 After 10 rounds with R²<0.70, consider model architecture changes.")

        return " | ".join(recommendations) if recommendations else "Continue training."

    def _calculate_health(
        self, r2: float, loss: float, client_metrics: Dict[str, Dict]
    ) -> str:
        """Calculate overall training health score."""

        # Score components (0-100 each)
        r2_score = min(r2 * 100, 100)

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
            r2_values = [m.get("train_r2", 0) for m in client_metrics.values()]
            if r2_values:
                consistency = 1 - (max(r2_values) - min(r2_values))
                consistency_score = consistency * 100
            else:
                consistency_score = 50
        else:
            consistency_score = 50

        # Overall score
        overall = (r2_score * 0.5) + (loss_score * 0.3) + (consistency_score * 0.2)

        if overall >= 90:
            return f"🟢 HEALTHY ({overall:.0f}/100)"
        elif overall >= 70:
            return f"🟡 GOOD ({overall:.0f}/100)"
        elif overall >= 50:
            return f"🟠 MODERATE ({overall:.0f}/100)"
        else:
            return f"🔴 NEEDS ATTENTION ({overall:.0f}/100)"

    def generate_session_summary(
        self, total_rounds: int, final_r2: float, final_loss: float
    ) -> str:
        """Generate end-of-session summary."""

        summary_parts = [
            f"═══════════════════════════════════════",
            f"FL TRAINING SESSION COMPLETE",
            f"═══════════════════════════════════════",
            f"Total Rounds: {total_rounds}",
            f"Final R²: {final_r2:.4f} ({self._classify_r2(final_r2).upper()})",
            f"Final Loss: {final_loss:.6f}",
        ]

        if len(self.round_history) > 1:
            initial_r2 = self.round_history[0]["r2"]
            r2_improvement = final_r2 - initial_r2
            summary_parts.append(f"R² Improvement: {r2_improvement*100:.2f}%")

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
