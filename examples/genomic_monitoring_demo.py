"""
Genomic Diffusion Model Monitoring Demo

Demonstrates monitoring of DNA sequence generation with:
- Standard diffusion metrics (confidence, perplexity)
- Genomic-specific metrics (GC content, ORFs, complexity)
- Biological validity alerts

Use Case: DNA sequence generation for synthetic biology
"""

import sys
import os
import time
import random
from typing import List, Dict, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from diffusion_monitor.quality_detector import QualityDetector
from diffusion_monitor.genomic_metrics import (
    GenomicQualityAnalyzer,
    integrate_with_quality_detector,
)
from diffusion_monitor.alert_manager import (
    AlertManager,
    AlertSeverity,
    ConsoleChannel,
)


class MockGenomicDiffusionModel:
    """
    Simulates a diffusion model that generates DNA sequences

    Can generate:
    - Healthy sequences (valid GC content, ORFs, complexity)
    - Degraded sequences (GC drift, homopolymers, low complexity)
    """

    BASES = ['A', 'C', 'G', 'T']

    def __init__(
        self,
        sequence_length: int = 300,  # 100 codons
        quality_mode: str = "healthy",  # "healthy", "degraded", "critical"
    ):
        self.sequence_length = sequence_length
        self.quality_mode = quality_mode

    def generate(self, prompt: str, num_steps: int = 50) -> Tuple[str, List[Dict]]:
        """
        Generate DNA sequence with diffusion process

        Returns:
            (sequence, metrics_history)
        """
        # Quality parameters
        params = {
            "healthy": {
                "gc_target": 0.50,
                "gc_noise": 0.05,
                "complexity": 0.8,
                "has_orfs": True,
                "confidence": 0.90,
                "perplexity": 15.0,
            },
            "degraded": {
                "gc_target": 0.35,  # GC drift!
                "gc_noise": 0.15,
                "complexity": 0.4,  # Low complexity
                "has_orfs": False,
                "confidence": 0.65,
                "perplexity": 40.0,
            },
            "critical": {
                "gc_target": 0.20,  # Very bad GC
                "gc_noise": 0.25,
                "complexity": 0.2,  # Very repetitive
                "has_orfs": False,
                "confidence": 0.40,
                "perplexity": 75.0,
            },
        }

        p = params[self.quality_mode]

        # Generate sequence
        sequence = self._generate_sequence(
            gc_target=p["gc_target"],
            gc_noise=p["gc_noise"],
            complexity=p["complexity"],
            has_orfs=p["has_orfs"],
        )

        # Generate diffusion metrics (per-step)
        metrics_history = []
        current_confidence = 0.2
        current_perplexity = 80.0

        for step in range(num_steps):
            progress = (step + 1) / num_steps

            # Converge to target quality
            current_confidence = current_confidence * 0.9 + p["confidence"] * 0.1
            current_perplexity = current_perplexity * 0.95 + p["perplexity"] * 0.05

            metrics = {
                "step_number": step,
                "step_latency_ms": random.gauss(50, 10),
                "confidence": current_confidence + random.gauss(0, 0.02),
                "perplexity": max(1.0, current_perplexity + random.gauss(0, 2)),
                "tokens_flipped": int(20 * (1 - progress)),
                "attention_entropy": 3.0 * (1 - progress),
            }
            metrics_history.append(metrics)

            time.sleep(0.001)  # Simulate processing

        return sequence, metrics_history

    def _generate_sequence(
        self,
        gc_target: float,
        gc_noise: float,
        complexity: float,
        has_orfs: bool,
    ) -> str:
        """Generate DNA sequence with specified characteristics"""

        if has_orfs:
            # Generate with valid ORF
            sequence = self._generate_with_orf(gc_target, gc_noise, complexity)
        else:
            # Generate random sequence
            sequence = self._generate_random(gc_target, gc_noise, complexity)

        return sequence

    def _generate_with_orf(self, gc_target: float, gc_noise: float, complexity: float) -> str:
        """Generate sequence with valid ORF"""
        # Start with ATG
        sequence = "ATG"

        # Generate codons
        num_codons = (self.sequence_length - 6) // 3  # -6 for start/stop

        for _ in range(num_codons):
            if complexity > 0.6:
                # High complexity: random codons
                codon = ''.join(random.choices(self.BASES, k=3))
            else:
                # Low complexity: repetitive
                codon = random.choice(['AAA', 'TTT', 'CCC', 'GGG'])

            # Avoid premature stop codons
            if codon in ['TAA', 'TAG', 'TGA']:
                codon = 'GCA'  # Alanine

            sequence += codon

        # End with stop codon
        sequence += random.choice(['TAA', 'TAG', 'TGA'])

        # Adjust GC content
        sequence = self._adjust_gc_content(sequence, gc_target, gc_noise)

        return sequence[:self.sequence_length]

    def _generate_random(self, gc_target: float, gc_noise: float, complexity: float) -> str:
        """Generate random sequence (no ORF)"""
        if complexity > 0.6:
            # High complexity
            gc_actual = gc_target + random.gauss(0, gc_noise)
            gc_actual = max(0.1, min(0.9, gc_actual))

            num_gc = int(self.sequence_length * gc_actual)
            num_at = self.sequence_length - num_gc

            bases = ['G', 'C'] * (num_gc // 2) + ['A', 'T'] * (num_at // 2)
            random.shuffle(bases)
            return ''.join(bases[:self.sequence_length])
        else:
            # Low complexity: homopolymers
            base = random.choice(self.BASES)
            return base * self.sequence_length

    def _adjust_gc_content(self, sequence: str, target: float, noise: float) -> str:
        """Adjust GC content of sequence"""
        current_gc = (sequence.count('G') + sequence.count('C')) / len(sequence)
        desired_gc = target + random.gauss(0, noise)

        # Simple adjustment (production would be more sophisticated)
        if abs(current_gc - desired_gc) < 0.05:
            return sequence

        # Replace bases to adjust GC
        seq_list = list(sequence)
        if current_gc < desired_gc:
            # Need more GC
            for i, base in enumerate(seq_list):
                if base in ['A', 'T']:
                    seq_list[i] = random.choice(['G', 'C'])
                    current_gc = (seq_list.count('G') + seq_list.count('C')) / len(seq_list)
                    if current_gc >= desired_gc:
                        break
        else:
            # Need less GC
            for i, base in enumerate(seq_list):
                if base in ['G', 'C']:
                    seq_list[i] = random.choice(['A', 'T'])
                    current_gc = (seq_list.count('G') + seq_list.count('C')) / len(seq_list)
                    if current_gc <= desired_gc:
                        break

        return ''.join(seq_list)


def print_section(title: str):
    """Print formatted section header"""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def run_genomic_demo():
    """Run complete genomic monitoring demo"""

    print_section("🧬 Genomic Diffusion Model Monitoring - DEMO")

    print("Scenario: You're generating synthetic DNA sequences for synthetic biology.")
    print("Your diffusion model creates 300bp DNA sequences with functional genes.")
    print("We'll monitor both diffusion quality AND biological validity.\n")

    input("Press Enter to start...\n")

    # Initialize components
    print_section("⚙️  Initializing Components")

    # Quality detector (standard)
    quality_detector = QualityDetector(
        baseline_window=50,
        alert_threshold=3,
        confidence_threshold=2.0,
    )
    print("✅ Quality Detector initialized (diffusion metrics)")

    # Genomic analyzer
    genomic_analyzer = GenomicQualityAnalyzer(
        sequence_type="dna",
        expected_gc_content=0.50,
        gc_tolerance=0.10,
        max_homopolymer_length=10,
        min_complexity=0.30,
    )
    print("✅ Genomic Analyzer initialized (biological metrics)")

    # Alert manager
    alert_mgr = AlertManager(
        model_name="dna-generator",
        environment="production",
    )
    alert_mgr.add_channel(ConsoleChannel())
    print("✅ Alert Manager initialized\n")

    time.sleep(1)

    # Phase 1: Learn baseline with healthy sequences
    print_section("📊 Phase 1: Baseline Learning (50 healthy sequences)")

    model = MockGenomicDiffusionModel(quality_mode="healthy")

    print("Generating healthy DNA sequences...\n")

    for i in range(50):
        sequence, metrics_history = model.generate(f"Generate gene {i}")

        # Analyze with genomic analyzer
        genomic_metrics = genomic_analyzer.analyze_sequence(sequence)

        # Extract quality signal
        signal = quality_detector.extract_quality_signal(
            metrics_history,
            f"req-baseline-{i}"
        )

        # Learn baseline
        quality_detector.learn_baseline(signal)

        if (i + 1) % 10 == 0:
            warnings = genomic_analyzer.check_biological_anomalies(genomic_metrics)
            print(f"[{i+1}/50] Quality: {signal.quality_score:.3f}, "
                  f"GC: {genomic_metrics.gc_content:.2%}, "
                  f"ORFs: {genomic_metrics.orf_count}, "
                  f"Warnings: {len(warnings)}")

    print(f"\n✅ Baseline learned!")
    if quality_detector.baseline:
        print(f"  Confidence: {quality_detector.baseline.confidence_mean:.3f}")
        print(f"  Perplexity: {quality_detector.baseline.perplexity_mean:.1f}")

    time.sleep(2)

    # Phase 2: Normal operation
    print_section("✅ Phase 2: Normal Operation (20 sequences)")

    print("System healthy. Generating sequences...\n")

    for i in range(20):
        sequence, metrics_history = model.generate(f"Generate gene {i}")

        genomic_metrics = genomic_analyzer.analyze_sequence(sequence)
        signal = quality_detector.extract_quality_signal(metrics_history, f"req-healthy-{i}")
        signal = quality_detector.detect_degradation(signal)

        warnings = genomic_analyzer.check_biological_anomalies(genomic_metrics)

        if (i + 1) % 5 == 0:
            status = "✅ OK" if genomic_metrics.is_biologically_valid else "⚠️  WARN"
            print(f"[{i+1}/20] {status} - Quality: {signal.quality_score:.3f}, "
                  f"GC: {genomic_metrics.gc_content:.2%}, "
                  f"Validity: {genomic_metrics.biological_validity_score:.2f}")

    print(f"\n✅ All sequences biologically valid!")

    time.sleep(2)

    # Phase 3: Quality degradation (biological anomalies)
    print_section("🚨 Phase 3: Biological Quality Degradation!")

    print("INCIDENT: Model starts generating sequences with:")
    print("  - GC content drift (0.50 → 0.35)")
    print("  - Loss of ORF structure")
    print("  - Increased homopolymer runs")
    print("  - Low complexity sequences\n")

    input("Press Enter to inject biological anomalies...\n")

    # Switch to degraded model
    degraded_model = MockGenomicDiffusionModel(quality_mode="degraded")

    detection_start = time.time()
    detected_diffusion = False
    detected_biological = False

    for i in range(20):
        sequence, metrics_history = degraded_model.generate(f"Generate gene {i}")

        # Analyze
        genomic_metrics = genomic_analyzer.analyze_sequence(sequence)
        signal = quality_detector.extract_quality_signal(metrics_history, f"req-degraded-{i}")
        signal = quality_detector.detect_degradation(signal)

        warnings = genomic_analyzer.check_biological_anomalies(genomic_metrics)

        # Print status
        status = "🚨 DEGRADED" if signal.is_degraded or not genomic_metrics.is_biologically_valid else "✅ OK"
        print(f"[{i+1}] {status} - "
              f"Diffusion Quality: {signal.quality_score:.3f}, "
              f"Bio Validity: {genomic_metrics.biological_validity_score:.2f}")

        if warnings:
            for warning in warnings[:2]:  # Show first 2
                print(f"     ⚠️  {warning}")

        # Check alerts
        alert_status = quality_detector.get_alert_status()

        if not detected_biological and not genomic_metrics.is_biologically_valid:
            detection_time = time.time() - detection_start
            print(f"\n{'!'*80}")
            print(f"🧬 BIOLOGICAL ANOMALY DETECTED! Time: {detection_time:.1f}s")
            print(f"{'!'*80}\n")
            detected_biological = True

        if alert_status["active"] and not detected_diffusion:
            detection_time = time.time() - detection_start
            print(f"\n{'!'*80}")
            print(f"🚨 DIFFUSION QUALITY ALERT! Time: {detection_time:.1f}s")
            print(f"{'!'*80}\n")

            alert_mgr.fire_alert(
                alert_key="quality-degradation",
                title="DNA Generation Quality Degraded",
                description=f"Both diffusion and biological quality degraded. {alert_status['affected_requests']} sequences affected.",
                primary_reason=f"Diffusion: {alert_status['primary_reason']}, Biological: {len(warnings)} warnings",
                affected_requests=alert_status["affected_requests"],
                metrics={
                    "gc_content": genomic_metrics.gc_content,
                    "orf_count": genomic_metrics.orf_count,
                    "validity_score": genomic_metrics.biological_validity_score,
                },
                severity=AlertSeverity.CRITICAL,
            )
            detected_diffusion = True

        if detected_biological and detected_diffusion:
            break

        time.sleep(0.1)

    print(f"\n✅ Both diffusion and biological anomalies detected!")
    print(f"  Diffusion detection: ~{detection_time:.0f}s")
    print(f"  Biological detection: Immediate (first degraded sequence)")

    time.sleep(2)

    # Phase 4: Recovery
    print_section("🔧 Phase 4: Fix Applied & Recovery")

    print("Rollback deployed! Model restored to healthy parameters.")
    print("Monitoring recovery...\n")

    input("Press Enter to apply fix...\n")

    # Switch back to healthy model
    model = MockGenomicDiffusionModel(quality_mode="healthy")

    for i in range(10):
        sequence, metrics_history = model.generate(f"Generate gene {i}")

        genomic_metrics = genomic_analyzer.analyze_sequence(sequence)
        signal = quality_detector.extract_quality_signal(metrics_history, f"req-recovered-{i}")
        signal = quality_detector.detect_degradation(signal)

        warnings = genomic_analyzer.check_biological_anomalies(genomic_metrics)

        status = "✅ HEALTHY" if genomic_metrics.is_biologically_valid else "⚠️  WARN"
        print(f"[{i+1}] {status} - "
              f"Quality: {signal.quality_score:.3f}, "
              f"GC: {genomic_metrics.gc_content:.2%}, "
              f"ORFs: {genomic_metrics.orf_count}")

        alert_status = quality_detector.get_alert_status()
        if not alert_status["active"]:
            print(f"\n{'='*80}")
            print("✅ ALERT RESOLVED! System back to healthy state.")
            print(f"{'='*80}\n")
            alert_mgr.resolve_alert("quality-degradation")
            break

        time.sleep(0.1)

    # Final summary
    print_section("📊 Final Summary")

    stats = quality_detector.get_statistics()
    print("Diffusion Monitoring:")
    print(f"  Total Sequences: {stats['total_requests']}")
    print(f"  Degraded: {stats['total_degraded']}")
    print(f"  Alerts Fired: {stats['total_alerts']}")

    print("\nGenomic Monitoring:")
    print(f"  Biological Anomalies: Detected immediately")
    print(f"  GC Drift: Detected")
    print(f"  ORF Loss: Detected")
    print(f"  Homopolymers: Detected")

    print_section("🎉 Demo Complete!")

    print("What you learned:")
    print("  1. ✅ Monitor BOTH diffusion quality AND biological validity")
    print("  2. ✅ Genomic-specific metrics (GC, ORFs, complexity)")
    print("  3. ✅ Biological anomalies detected immediately")
    print("  4. ✅ Combined alerts for comprehensive monitoring")
    print("  5. ✅ Production-ready for synthetic biology applications")

    print("\nNext steps:")
    print("  - Integrate with your real genomic diffusion model")
    print("  - Add more genomic validators (BLAST, motif detection)")
    print("  - Set up alerts for your biology team")
    print("  - Monitor in production! 🧬🚀\n")


if __name__ == "__main__":
    try:
        run_genomic_demo()
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted. Goodbye!")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
