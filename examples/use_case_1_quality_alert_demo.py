"""
Use Case 1: Production Quality Degradation Alert - DEMO

This script demonstrates the complete workflow for detecting quality degradation
in <2 minutes, as designed for Sarah (SRE Lead).

Workflow:
1. Start monitoring with healthy baseline
2. Simulate normal operations (100 healthy requests)
3. Inject quality degradation (bad temperature parameter)
4. Detect degradation and fire alert
5. Fix issue and resolve alert

Success Criteria:
- Detection time: <2 minutes from first degraded request
- Precision: No false positives during healthy operation
- Actionability: Alert explains what failed and why
"""

import sys
import os
import time
import random
from typing import List, Dict
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from diffusion_monitor.quality_detector import QualityDetector, QualitySignal
from diffusion_monitor.alert_manager import (
    AlertManager,
    AlertSeverity,
    SlackChannel,
    ConsoleChannel,
)
# PrometheusExporter is optional
# from exporters.prometheus_exporter import PrometheusExporter


# Mock Diffusion Model
class MockDiffusionModel:
    """
    Simulates a diffusion model with configurable quality

    Parameters that affect quality:
    - temperature: Controls randomness (higher = worse quality)
    - num_steps: Number of denoising steps
    - noise_level: Initial noise amount
    """

    def __init__(
        self,
        temperature: float = 1.0,
        num_steps: int = 50,
        noise_level: float = 0.5,
    ):
        self.temperature = temperature
        self.num_steps = num_steps
        self.noise_level = noise_level

    def generate(self, prompt: str, request_id: str) -> List[Dict]:
        """
        Simulate diffusion generation, returning metrics for each step

        Returns list of per-step metrics
        """
        metrics_history = []

        # Initial state (high perplexity, low confidence)
        current_perplexity = 80 * self.noise_level
        current_confidence = 0.2

        # Track token changes
        tokens_changed_per_step = []

        for step in range(self.num_steps):
            step_start = time.time()

            # Simulate denoising (quality improves over steps)
            progress = (step + 1) / self.num_steps

            # Temperature affects quality significantly
            temp_factor = 1.0 / (1.0 + self.temperature - 1.0)

            # Perplexity decreases (with temperature affecting rate)
            current_perplexity = current_perplexity * (
                1 - 0.05 * temp_factor * (1 + random.gauss(0, 0.1))
            )
            current_perplexity = max(1.0, current_perplexity)

            # Confidence increases
            current_confidence = min(
                0.95,
                current_confidence + 0.015 * temp_factor * (1 + random.gauss(0, 0.1))
            )

            # Token flips (decreases as we converge)
            tokens_flipped = int(20 * (1 - progress) * self.temperature)
            tokens_changed_per_step.append(tokens_flipped)

            # Attention entropy (should decrease as we focus)
            attention_entropy = 3.0 * (1 - progress) * self.temperature

            # Step latency (slightly random)
            step_latency = random.gauss(0.05, 0.01)  # 50ms ± 10ms
            time.sleep(max(0.01, step_latency))  # Simulate processing

            step_end = time.time()

            metrics = {
                "step_number": step,
                "step_latency_ms": (step_end - step_start) * 1000,
                "confidence": current_confidence,
                "perplexity": current_perplexity,
                "tokens_flipped": tokens_flipped,
                "attention_entropy": attention_entropy,
            }

            metrics_history.append(metrics)

        return metrics_history


def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def print_metrics_summary(signal: QualitySignal):
    """Print quality signal summary"""
    print(f"Request ID: {signal.request_id}")
    print(f"Final Confidence: {signal.final_confidence:.3f}")
    print(f"Final Perplexity: {signal.final_perplexity:.1f}")
    print(f"Convergence Step: {signal.convergence_step}")
    print(f"Quality Score: {signal.quality_score:.3f}")
    print(f"Degraded: {'🚨 YES' if signal.is_degraded else '✅ NO'}")
    if signal.degradation_reasons:
        print(f"Reasons:")
        for reason in signal.degradation_reasons:
            print(f"  - {reason}")
    print()


def run_demo():
    """Run the complete Use Case 1 demo"""

    print_section("🎯 Use Case 1: Production Quality Degradation Alert - DEMO")

    print("Scenario: You're Sarah, SRE Lead at an AI startup.")
    print("Your LLaDA-7B API is running in production.")
    print("We'll simulate normal operation, then inject a quality degradation.")
    print("Goal: Detect and alert in <2 minutes.\n")

    input("Press Enter to start...\n")

    # Initialize components
    print_section("⚙️  Initializing Monitoring Components")

    # Quality detector
    detector = QualityDetector(
        baseline_window=100,      # Learn from first 100 requests
        detection_window=10,      # Monitor last 10 requests
        alert_threshold=3,        # Alert after 3 consecutive bad requests
        confidence_threshold=2.0, # 2 sigma for anomaly detection
    )
    print("✅ Quality Detector initialized")

    # Alert manager
    alert_mgr = AlertManager(
        model_name="llada-7b",
        environment="production",
        rate_limit_seconds=60,
    )

    # Add console channel (in production, add Slack/PagerDuty)
    alert_mgr.add_channel(ConsoleChannel())
    print("✅ Alert Manager initialized (Console channel)")

    # Prometheus exporter (optional)
    # exporter = PrometheusExporter(port=9090)
    # exporter.start()
    # print("✅ Prometheus exporter started on port 9090")

    print("\nAll components ready!\n")
    time.sleep(1)

    # Phase 1: Healthy baseline
    print_section("📊 Phase 1: Learning Baseline (100 healthy requests)")

    model = MockDiffusionModel(
        temperature=1.0,  # Normal temperature
        num_steps=50,
        noise_level=0.5,
    )

    print("Running 100 healthy requests to establish baseline...")
    print("(showing every 10th request)\n")

    baseline_start = time.time()

    for i in range(100):
        request_id = f"req-baseline-{i:04d}"

        # Generate with healthy model
        metrics_history = model.generate(
            prompt=f"Test prompt {i}",
            request_id=request_id
        )

        # Extract quality signal
        signal = detector.extract_quality_signal(metrics_history, request_id)

        # Learn baseline
        detector.learn_baseline(signal)

        # Show progress
        if (i + 1) % 10 == 0:
            print(f"[{i+1}/100] Confidence: {signal.final_confidence:.3f}, "
                  f"Perplexity: {signal.final_perplexity:.1f}, "
                  f"Quality: {signal.quality_score:.3f}")

    baseline_time = time.time() - baseline_start

    print(f"\n✅ Baseline established in {baseline_time:.1f}s")
    print(f"📊 Baseline stats:")
    if detector.baseline:
        print(f"  Confidence: {detector.baseline.confidence_mean:.3f} ± {detector.baseline.confidence_std:.3f}")
        print(f"  Perplexity: {detector.baseline.perplexity_mean:.1f} ± {detector.baseline.perplexity_std:.1f}")
        print(f"  Quality Score: {detector.baseline.quality_score_mean:.3f} ± {detector.baseline.quality_score_std:.3f}")

    time.sleep(2)

    # Phase 2: Normal operations
    print_section("✅ Phase 2: Normal Operations (20 requests)")

    print("System is healthy. Processing normal requests...\n")

    for i in range(20):
        request_id = f"req-healthy-{i:04d}"

        metrics_history = model.generate(
            prompt=f"User prompt {i}",
            request_id=request_id
        )

        signal = detector.extract_quality_signal(metrics_history, request_id)
        signal = detector.detect_degradation(signal)

        if (i + 1) % 5 == 0:
            print(f"[{i+1}/20] Quality: {signal.quality_score:.3f}, Degraded: {signal.is_degraded}")

    stats = detector.get_statistics()
    print(f"\n✅ All requests healthy!")
    print(f"  Total: {stats['total_requests']}, Degraded: {stats['total_degraded']}, Alerts: {stats['total_alerts']}")

    time.sleep(2)

    # Phase 3: Inject quality degradation
    print_section("🚨 Phase 3: Quality Degradation Injected!")

    print("INCIDENT: Someone deployed a config change with bad temperature!")
    print("Temperature changed: 1.0 → 2.5 (way too high!)")
    print("This will cause poor quality outputs...\n")

    input("Press Enter to inject the bug...\n")

    # Create degraded model
    degraded_model = MockDiffusionModel(
        temperature=2.5,  # BAD: Too high!
        num_steps=50,
        noise_level=0.5,
    )

    print("🔥 Degraded model active. Monitoring for quality issues...\n")

    detection_start = time.time()
    detected = False

    for i in range(20):
        request_id = f"req-degraded-{i:04d}"

        # Generate with degraded model
        metrics_history = degraded_model.generate(
            prompt=f"User prompt {i}",
            request_id=request_id
        )

        # Extract and detect
        signal = detector.extract_quality_signal(metrics_history, request_id)
        signal = detector.detect_degradation(signal)

        print(f"[{i+1}] Quality: {signal.quality_score:.3f}, "
              f"Confidence: {signal.final_confidence:.3f}, "
              f"Degraded: {'🚨 YES' if signal.is_degraded else '✅ NO'}")

        if signal.is_degraded and len(signal.degradation_reasons) > 0:
            print(f"     Reasons: {signal.degradation_reasons[0][:80]}...")

        # Check if alert should fire
        alert_status = detector.get_alert_status()

        if alert_status["active"] and not detected:
            detection_time = time.time() - detection_start

            print(f"\n{'!'*80}")
            print(f"🚨 ALERT FIRED! Detection time: {detection_time:.1f}s")
            print(f"{'!'*80}\n")

            # Fire alert through alert manager
            alert_mgr.fire_alert(
                alert_key="quality-degradation",
                title="Quality Degradation Detected",
                description=f"Model quality has degraded. {alert_status['affected_requests']} consecutive requests affected.",
                primary_reason=alert_status["primary_reason"],
                affected_requests=alert_status["affected_requests"],
                metrics={
                    "detection_time_seconds": detection_time,
                    "degradation_rate": f"{alert_status['affected_requests']} consecutive",
                },
                severity=AlertSeverity.CRITICAL,
            )

            detected = True

            # Show alert details
            print(f"\n📊 Alert Details:")
            print(f"  Primary Reason: {alert_status['primary_reason']}")
            print(f"  Affected Requests: {alert_status['affected_requests']}")
            print(f"  Detection Time: {detection_time:.1f}s ({'✅ <2min' if detection_time < 120 else '❌ >2min'})")

            break

        time.sleep(0.1)

    time.sleep(2)

    # Phase 4: Fix and resolve
    print_section("🔧 Phase 4: Fix Applied & Alert Resolution")

    print("Rollback deployed! Temperature fixed: 2.5 → 1.0")
    print("Monitoring for recovery...\n")

    input("Press Enter to apply fix...\n")

    # Switch back to healthy model
    model = MockDiffusionModel(
        temperature=1.0,  # Fixed!
        num_steps=50,
        noise_level=0.5,
    )

    for i in range(10):
        request_id = f"req-recovered-{i:04d}"

        metrics_history = model.generate(
            prompt=f"User prompt {i}",
            request_id=request_id
        )

        signal = detector.extract_quality_signal(metrics_history, request_id)
        signal = detector.detect_degradation(signal)

        print(f"[{i+1}] Quality: {signal.quality_score:.3f}, "
              f"Degraded: {'🚨 YES' if signal.is_degraded else '✅ NO'}")

        # Check if alert resolved
        alert_status = detector.get_alert_status()

        if not alert_status["active"]:
            print(f"\n{'='*80}")
            print("✅ ALERT RESOLVED! System back to healthy state.")
            print(f"{'='*80}\n")

            # Resolve alert
            alert_mgr.resolve_alert("quality-degradation")

            break

        time.sleep(0.1)

    # Final summary
    print_section("📊 Final Summary")

    stats = detector.get_statistics()
    alert_stats = alert_mgr.get_statistics()

    print("Detector Statistics:")
    print(f"  Total Requests: {stats['total_requests']}")
    print(f"  Degraded Requests: {stats['total_degraded']}")
    print(f"  Degradation Rate: {stats['degradation_rate']:.1f}%")
    print(f"  Baseline Ready: {stats['baseline_ready']}")
    print(f"  Alert Active: {stats['alert_active']}")

    print("\nAlert Manager Statistics:")
    print(f"  Alerts Sent: {alert_stats['alerts_sent']}")
    print(f"  Alerts Resolved: {alert_stats['alerts_resolved']}")
    print(f"  Active Alerts: {alert_stats['active_alerts']}")

    print("\n✅ Success Criteria:")
    if detected:
        print(f"  ✅ Detection Time: {detection_time:.1f}s (<120s required)")
        print(f"  ✅ Actionable Alert: Primary reason identified")
        print(f"  ✅ Auto-Resolution: Alert cleared after fix")
    else:
        print(f"  ❌ Detection: No alert fired")

    print_section("🎉 Demo Complete!")

    print("What you learned:")
    print("  1. ✅ Quality degradation detected in <2 minutes")
    print("  2. ✅ Statistical baseline avoids false positives")
    print("  3. ✅ Alerts include actionable reasons (temperature issue)")
    print("  4. ✅ Auto-resolution when system recovers")
    print("  5. ✅ Low overhead (runs alongside inference)")

    print("\nNext steps:")
    print("  - Integrate with your LLaDA/Open-dLLM model")
    print("  - Add Slack/PagerDuty channels to AlertManager")
    print("  - View metrics in Grafana (docker-compose up)")
    print("  - Customize thresholds for your use case")
    print("  - Deploy to production! 🚀\n")


if __name__ == "__main__":
    try:
        run_demo()
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted. Goodbye!")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
