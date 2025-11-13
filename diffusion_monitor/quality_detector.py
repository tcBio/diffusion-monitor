"""
Quality Detector for Diffusion Models

Detects quality degradation in real-time using statistical baselines and smart thresholds.
Designed for Use Case 1: Production Quality Alerts (<2 min detection time).
"""

import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import deque
import numpy as np
from scipy import stats


@dataclass
class QualitySignal:
    """Quality indicators extracted from diffusion metrics"""

    timestamp: float
    request_id: str

    # Core quality metrics
    final_confidence: float      # Final step confidence (higher = better)
    final_perplexity: float      # Final step perplexity (lower = better)
    convergence_step: int        # Step where quality plateaued (lower = faster)
    total_token_flips: int       # Total tokens that changed (lower = more stable)

    # Step-wise analysis
    confidence_trend: float      # Linear regression slope of confidence
    perplexity_spike_count: int  # Number of perplexity spikes
    attention_entropy: float     # Attention pattern entropy

    # Derived quality score (0-1, higher = better)
    quality_score: float

    # Alert flags
    is_degraded: bool
    degradation_reasons: List[str]


@dataclass
class QualityBaseline:
    """Statistical baseline for quality metrics"""

    # Mean and std for each metric
    confidence_mean: float
    confidence_std: float
    perplexity_mean: float
    perplexity_std: float
    convergence_mean: float
    convergence_std: float
    quality_score_mean: float
    quality_score_std: float

    # Sample size
    n_samples: int
    last_updated: float

    def is_anomalous(self, metric_name: str, value: float, n_sigma: float = 2.0) -> bool:
        """Check if a value is anomalous (n_sigma standard deviations from mean)"""
        mean = getattr(self, f"{metric_name}_mean")
        std = getattr(self, f"{metric_name}_std")

        # Handle low/high being bad differently
        if metric_name == "perplexity":
            # High perplexity is bad
            return value > (mean + n_sigma * std)
        else:
            # Low values are bad (confidence, quality_score)
            return value < (mean - n_sigma * std)


class QualityDetector:
    """
    Real-time quality degradation detector

    Features:
    - Learns baseline from initial "good" requests
    - Detects anomalies using statistical thresholds
    - Tracks consecutive degradations to avoid false positives
    - Provides actionable degradation reasons
    """

    def __init__(
        self,
        baseline_window: int = 100,
        detection_window: int = 10,
        alert_threshold: int = 3,
        confidence_threshold: float = 2.0,
    ):
        """
        Initialize quality detector

        Args:
            baseline_window: Number of requests to learn baseline from
            detection_window: Rolling window for detection (recent requests)
            alert_threshold: Number of consecutive degraded requests before alerting
            confidence_threshold: Number of standard deviations for anomaly detection
        """
        self.baseline_window = baseline_window
        self.detection_window = detection_window
        self.alert_threshold = alert_threshold
        self.confidence_threshold = confidence_threshold

        # Storage
        self.baseline_signals: deque = deque(maxlen=baseline_window)
        self.recent_signals: deque = deque(maxlen=detection_window)
        self.baseline: Optional[QualityBaseline] = None

        # Alert state
        self.consecutive_degraded = 0
        self.alert_active = False
        self.alert_start_time: Optional[float] = None

        # Statistics
        self.total_requests = 0
        self.total_degraded = 0
        self.total_alerts = 0

    def compute_quality_score(self, metrics: Dict) -> float:
        """
        Compute overall quality score (0-1) from raw metrics

        Combines multiple signals into single score:
        - Final confidence (40%)
        - Inverse perplexity (30%)
        - Convergence speed (20%)
        - Token stability (10%)
        """
        # Normalize confidence (assumes 0-1 range)
        conf_score = metrics.get("final_confidence", 0.5)

        # Normalize perplexity (lower is better, typical range 1-100)
        perp = metrics.get("final_perplexity", 50)
        perp_score = max(0, 1 - (perp / 100))

        # Normalize convergence step (lower is better, assume max 50 steps)
        conv_step = metrics.get("convergence_step", 50)
        conv_score = max(0, 1 - (conv_step / 50))

        # Normalize token flips (lower is better, assume max 100 flips)
        flips = metrics.get("total_token_flips", 50)
        flip_score = max(0, 1 - (flips / 100))

        # Weighted combination
        quality_score = (
            0.40 * conf_score +
            0.30 * perp_score +
            0.20 * conv_score +
            0.10 * flip_score
        )

        return quality_score

    def extract_quality_signal(self, metrics_history: List[Dict], request_id: str) -> QualitySignal:
        """Extract quality signal from diffusion metrics history"""

        if not metrics_history:
            raise ValueError("Empty metrics history")

        # Get final step metrics
        final_step = metrics_history[-1]

        # Extract core metrics
        final_confidence = final_step.get("confidence", 0.0)
        final_perplexity = final_step.get("perplexity", float('inf'))

        # Find convergence step (where quality stops improving significantly)
        convergence_step = self._find_convergence_step(metrics_history)

        # Count total token flips
        total_token_flips = sum(m.get("tokens_flipped", 0) for m in metrics_history)

        # Compute confidence trend (is it improving?)
        confidences = [m.get("confidence", 0) for m in metrics_history]
        confidence_trend = np.polyfit(range(len(confidences)), confidences, 1)[0] if len(confidences) > 1 else 0

        # Count perplexity spikes (increases between steps)
        perplexities = [m.get("perplexity", 0) for m in metrics_history]
        perplexity_spike_count = sum(
            1 for i in range(1, len(perplexities))
            if perplexities[i] > perplexities[i-1] * 1.2
        )

        # Get attention entropy (if available)
        attention_entropy = final_step.get("attention_entropy", 0.0)

        # Compute overall quality score
        quality_score = self.compute_quality_score({
            "final_confidence": final_confidence,
            "final_perplexity": final_perplexity,
            "convergence_step": convergence_step,
            "total_token_flips": total_token_flips,
        })

        return QualitySignal(
            timestamp=time.time(),
            request_id=request_id,
            final_confidence=final_confidence,
            final_perplexity=final_perplexity,
            convergence_step=convergence_step,
            total_token_flips=total_token_flips,
            confidence_trend=confidence_trend,
            perplexity_spike_count=perplexity_spike_count,
            attention_entropy=attention_entropy,
            quality_score=quality_score,
            is_degraded=False,
            degradation_reasons=[],
        )

    def _find_convergence_step(self, metrics_history: List[Dict], threshold: float = 0.05) -> int:
        """Find step where quality improvement becomes marginal"""

        if len(metrics_history) < 3:
            return len(metrics_history)

        confidences = [m.get("confidence", 0) for m in metrics_history]

        # Find first step where improvement is <threshold
        for i in range(1, len(confidences)):
            improvement = confidences[i] - confidences[i-1]
            if improvement < threshold:
                return i

        return len(confidences)

    def learn_baseline(self, signal: QualitySignal):
        """Add signal to baseline learning"""

        self.baseline_signals.append(signal)

        # Recompute baseline if we have enough samples
        if len(self.baseline_signals) >= min(10, self.baseline_window // 2):
            self._compute_baseline()

    def _compute_baseline(self):
        """Compute statistical baseline from collected signals"""

        signals = list(self.baseline_signals)

        # Extract metrics
        confidences = [s.final_confidence for s in signals]
        perplexities = [s.final_perplexity for s in signals]
        convergences = [s.convergence_step for s in signals]
        quality_scores = [s.quality_score for s in signals]

        # Compute statistics (using robust estimators)
        self.baseline = QualityBaseline(
            confidence_mean=np.median(confidences),
            confidence_std=stats.median_abs_deviation(confidences, scale='normal'),
            perplexity_mean=np.median(perplexities),
            perplexity_std=stats.median_abs_deviation(perplexities, scale='normal'),
            convergence_mean=np.median(convergences),
            convergence_std=stats.median_abs_deviation(convergences, scale='normal'),
            quality_score_mean=np.median(quality_scores),
            quality_score_std=stats.median_abs_deviation(quality_scores, scale='normal'),
            n_samples=len(signals),
            last_updated=time.time(),
        )

    def detect_degradation(self, signal: QualitySignal) -> QualitySignal:
        """
        Detect if signal indicates quality degradation

        Returns updated signal with is_degraded and degradation_reasons set
        """

        self.total_requests += 1

        # If baseline not ready, continue learning
        if self.baseline is None or len(self.baseline_signals) < self.baseline_window:
            self.learn_baseline(signal)
            return signal

        # Check for anomalies
        reasons = []

        # Check confidence
        if self.baseline.is_anomalous("confidence", signal.final_confidence, self.confidence_threshold):
            reasons.append(
                f"Low confidence: {signal.final_confidence:.3f} "
                f"(baseline: {self.baseline.confidence_mean:.3f} ± {self.baseline.confidence_std:.3f})"
            )

        # Check perplexity
        if self.baseline.is_anomalous("perplexity", signal.final_perplexity, self.confidence_threshold):
            reasons.append(
                f"High perplexity: {signal.final_perplexity:.1f} "
                f"(baseline: {self.baseline.perplexity_mean:.1f} ± {self.baseline.perplexity_std:.1f})"
            )

        # Check overall quality score
        if self.baseline.is_anomalous("quality_score", signal.quality_score, self.confidence_threshold):
            reasons.append(
                f"Low quality score: {signal.quality_score:.3f} "
                f"(baseline: {self.baseline.quality_score_mean:.3f} ± {self.baseline.quality_score_std:.3f})"
            )

        # Additional heuristics
        if signal.perplexity_spike_count > 3:
            reasons.append(f"Unstable convergence: {signal.perplexity_spike_count} perplexity spikes")

        if signal.confidence_trend < -0.01:
            reasons.append(f"Decreasing confidence trend: {signal.confidence_trend:.4f}")

        # Mark as degraded if any reason found
        signal.is_degraded = len(reasons) > 0
        signal.degradation_reasons = reasons

        if signal.is_degraded:
            self.total_degraded += 1

        # Update recent signals
        self.recent_signals.append(signal)

        # Check for alert condition (consecutive degradations)
        self._check_alert_condition()

        return signal

    def _check_alert_condition(self):
        """Check if we should fire an alert (consecutive degraded requests)"""

        if len(self.recent_signals) < self.alert_threshold:
            return

        # Check last N signals
        recent = list(self.recent_signals)[-self.alert_threshold:]
        consecutive_bad = all(s.is_degraded for s in recent)

        if consecutive_bad and not self.alert_active:
            # Fire alert
            self.alert_active = True
            self.alert_start_time = time.time()
            self.total_alerts += 1
        elif not consecutive_bad and self.alert_active:
            # Resolve alert
            self.alert_active = False
            self.alert_start_time = None

    def get_alert_status(self) -> Dict:
        """Get current alert status"""

        if not self.alert_active:
            return {
                "active": False,
                "message": "System healthy",
            }

        # Get recent degraded signals
        recent_degraded = [s for s in self.recent_signals if s.is_degraded]

        # Aggregate reasons
        all_reasons = []
        for signal in recent_degraded[-self.alert_threshold:]:
            all_reasons.extend(signal.degradation_reasons)

        # Count reason frequency
        reason_counts = {}
        for reason in all_reasons:
            key = reason.split(":")[0]  # Extract reason type
            reason_counts[key] = reason_counts.get(key, 0) + 1

        # Find most common reason
        primary_reason = max(reason_counts.items(), key=lambda x: x[1])[0] if reason_counts else "Unknown"

        duration = time.time() - self.alert_start_time if self.alert_start_time else 0

        return {
            "active": True,
            "duration_seconds": duration,
            "affected_requests": len(recent_degraded),
            "primary_reason": primary_reason,
            "all_reasons": list(set([r.split(":")[0] for r in all_reasons])),
            "recent_signals": [asdict(s) for s in recent_degraded[-5:]],
        }

    def get_statistics(self) -> Dict:
        """Get detector statistics"""

        degradation_rate = (self.total_degraded / self.total_requests * 100) if self.total_requests > 0 else 0

        return {
            "total_requests": self.total_requests,
            "total_degraded": self.total_degraded,
            "degradation_rate": degradation_rate,
            "total_alerts": self.total_alerts,
            "baseline_ready": self.baseline is not None,
            "baseline_samples": len(self.baseline_signals),
            "alert_active": self.alert_active,
        }
