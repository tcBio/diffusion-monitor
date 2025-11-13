"""
Plant WGS Quality Monitor for FASTQ.GZ Files

Handles gzipped FASTQ files from real sequencing runs.
Extracts both sequence data AND quality scores.

Usage:
    python monitor_fastq.py sample.fastq.gz
    python monitor_fastq.py --batch /path/to/data/*.fastq.gz
"""

import sys
import os
import gzip
from typing import List, Tuple, Dict
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from diffusion_monitor.plant_genomics import PlantGenomicsAnalyzer
from diffusion_monitor.alert_manager import AlertManager, ConsoleChannel, SlackChannel


class FASTQParser:
    """Parse FASTQ and FASTQ.GZ files"""

    @staticmethod
    def parse_fastq(file_path: str, max_reads: int = None) -> Tuple[str, List[int]]:
        """
        Parse FASTQ or FASTQ.GZ file

        Args:
            file_path: Path to .fastq or .fastq.gz file
            max_reads: Maximum number of reads to process (None = all)

        Returns:
            (concatenated_sequence, quality_scores)
        """
        # Determine if gzipped
        is_gzipped = file_path.endswith('.gz')

        # Open file
        if is_gzipped:
            f = gzip.open(file_path, 'rt')  # 'rt' = read text mode
        else:
            f = open(file_path, 'r')

        sequences = []
        qualities = []

        try:
            line_num = 0
            read_count = 0

            while True:
                # FASTQ format has 4 lines per read:
                # Line 1: @Header
                # Line 2: Sequence
                # Line 3: +
                # Line 4: Quality scores

                header = f.readline()
                if not header:
                    break  # End of file

                sequence = f.readline().strip()
                plus = f.readline()
                quality = f.readline().strip()

                if not sequence or not quality:
                    break

                sequences.append(sequence)

                # Convert quality scores from ASCII to Phred scores
                # Phred+33 encoding: ASCII value - 33 = quality score
                qual_scores = [ord(q) - 33 for q in quality]
                qualities.extend(qual_scores)

                read_count += 1
                if max_reads and read_count >= max_reads:
                    break

                # Progress indicator for large files
                if read_count % 10000 == 0:
                    print(f"  Processed {read_count:,} reads...", end='\r')

        finally:
            f.close()

        # Concatenate all sequences
        full_sequence = ''.join(sequences)

        print(f"  Loaded {read_count:,} reads, {len(full_sequence):,} bases")

        return full_sequence, qualities

    @staticmethod
    def calculate_quality_stats(quality_scores: List[int]) -> Dict:
        """Calculate quality statistics from Phred scores"""
        import numpy as np

        if not quality_scores:
            return {
                "mean_quality": 0.0,
                "median_quality": 0.0,
                "min_quality": 0,
                "max_quality": 0,
                "q20_percent": 0.0,  # % bases with Q>=20
                "q30_percent": 0.0,  # % bases with Q>=30
            }

        scores = np.array(quality_scores)

        return {
            "mean_quality": float(np.mean(scores)),
            "median_quality": float(np.median(scores)),
            "min_quality": int(np.min(scores)),
            "max_quality": int(np.max(scores)),
            "q20_percent": float(np.sum(scores >= 20) / len(scores) * 100),
            "q30_percent": float(np.sum(scores >= 30) / len(scores) * 100),
        }


def analyze_wgs_file(
    fastq_path: str,
    analyzer: PlantGenomicsAnalyzer,
    max_reads: int = None,
) -> Dict:
    """
    Analyze a single FASTQ.GZ file

    Args:
        fastq_path: Path to .fastq.gz file
        analyzer: PlantGenomicsAnalyzer instance
        max_reads: Limit number of reads (None = all)

    Returns:
        Dict with analysis results
    """
    print(f"\n{'='*80}")
    print(f"Analyzing: {os.path.basename(fastq_path)}")
    print(f"{'='*80}")

    # Parse FASTQ
    print("Loading FASTQ data...")
    sequence, quality_scores = FASTQParser.parse_fastq(fastq_path, max_reads)

    # Calculate quality stats
    qual_stats = FASTQParser.calculate_quality_stats(quality_scores)

    print(f"\nSequencing Quality:")
    print(f"  Mean Quality: {qual_stats['mean_quality']:.1f}")
    print(f"  Q20 bases: {qual_stats['q20_percent']:.1f}%")
    print(f"  Q30 bases: {qual_stats['q30_percent']:.1f}%")

    # Analyze with plant genomics analyzer
    print(f"\nAnalyzing genomic content...")

    # For WGS data, we can add quality metrics
    wgs_metrics = {
        "mean_quality": qual_stats["mean_quality"],
        "q30_percent": qual_stats["q30_percent"],
    }

    plant_metrics = analyzer.analyze_plant_sequence(
        sequence=sequence,
        wgs_metrics=wgs_metrics,
    )

    # Print results
    print(f"\n{'─'*80}")
    print("GENOMIC ANALYSIS RESULTS")
    print(f"{'─'*80}")

    print(f"\n📊 Sequence Composition:")
    print(f"  Genome Size: {plant_metrics.genome_size_estimate:,} bp ({plant_metrics.genome_size_estimate/1e6:.1f} Mbp)")
    print(f"  GC Content: {plant_metrics.genomic_metrics.gc_content:.2%}")
    print(f"  Complexity Score: {plant_metrics.genomic_metrics.complexity_score:.2f}")
    print(f"  Max Homopolymer: {plant_metrics.genomic_metrics.homopolymer_max_length} bases")
    print(f"  N-content: {plant_metrics.genomic_metrics.n_content:.2%}")

    print(f"\n🧬 Gene Structure:")
    print(f"  ORF Count: {plant_metrics.genomic_metrics.orf_count}")
    print(f"  Start Codon: {'✅ Yes' if plant_metrics.genomic_metrics.has_valid_start_codon else '❌ No'}")
    print(f"  Stop Codon: {'✅ Yes' if plant_metrics.genomic_metrics.has_valid_stop_codon else '❌ No'}")

    print(f"\n🌱 Plant-Specific Metrics:")
    print(f"  Secondary Metabolite Genes: {plant_metrics.secondary_metabolite_gene_count}")
    print(f"  Terpene Synthases: {plant_metrics.terpene_synthase_count}")
    print(f"  Heterozygosity: {plant_metrics.heterozygosity_rate:.4f}")
    print(f"  Repeat Content: {plant_metrics.repeat_content:.2%}")

    print(f"\n⭐ Quality Scores:")
    print(f"  Sequencing Quality: {qual_stats['mean_quality']:.1f} (Q{int(qual_stats['mean_quality'])})")
    print(f"  Biological Validity: {plant_metrics.genomic_metrics.biological_validity_score:.2f}")
    print(f"  Training Data Quality: {plant_metrics.training_data_quality:.2f}")
    print(f"  Overall Quality: {(qual_stats['mean_quality']/40 + plant_metrics.training_data_quality)/2:.2f}")

    print(f"\n{'─'*80}")

    # Verdict
    is_high_qual = (
        plant_metrics.is_valid_plant_genome and
        qual_stats["q30_percent"] > 80 and
        plant_metrics.training_data_quality > 0.7
    )

    if is_high_qual:
        verdict = "✅ HIGH QUALITY - Suitable for analysis"
        verdict_color = "GREEN"
    elif plant_metrics.training_data_quality > 0.5:
        verdict = "⚠️  MEDIUM QUALITY - Review recommended"
        verdict_color = "YELLOW"
    else:
        verdict = "❌ LOW QUALITY - Do not use"
        verdict_color = "RED"

    print(f"\n🎯 VERDICT: {verdict}")

    # Warnings
    if plant_metrics.quality_warnings:
        print(f"\n⚠️  WARNINGS:")
        for warning in plant_metrics.quality_warnings:
            print(f"  - {warning}")

    if qual_stats["q30_percent"] < 80:
        print(f"  - Low sequencing quality: {qual_stats['q30_percent']:.1f}% Q30 (expected >80%)")

    if qual_stats["mean_quality"] < 30:
        print(f"  - Mean quality below Q30: {qual_stats['mean_quality']:.1f}")

    print(f"\n{'='*80}\n")

    return {
        "file": fastq_path,
        "verdict": verdict_color,
        "plant_metrics": plant_metrics,
        "qual_stats": qual_stats,
        "is_high_quality": is_high_qual,
    }


def batch_analyze(
    file_pattern: str,
    output_report: str = "wgs_quality_report.txt",
    max_reads_per_file: int = 100000,  # Limit for speed
    slack_webhook: str = None,
):
    """
    Analyze multiple FASTQ.GZ files

    Args:
        file_pattern: Glob pattern for files (e.g., "/data/*.fastq.gz")
        output_report: Output report filename
        max_reads_per_file: Limit reads per file for speed
        slack_webhook: Optional Slack webhook URL for alerts
    """
    import glob
    import time

    # Find files
    files = glob.glob(file_pattern)
    print(f"\n🔍 Found {len(files)} FASTQ files to analyze\n")

    if not files:
        print(f"❌ No files found matching: {file_pattern}")
        return

    # Initialize analyzer
    print("Initializing Plant Genomics Analyzer...")
    analyzer = PlantGenomicsAnalyzer(
        expected_coverage=30.0,
        min_mapping_quality=30.0,
    )

    # Customize for your plant
    analyzer.EXPECTED_GENOME_SIZE = 850_000_000  # 850 Mbp
    analyzer.EXPECTED_GC_CONTENT = 0.36
    analyzer.EXPECTED_HETEROZYGOSITY = 0.003

    # Initialize alert manager
    alert_mgr = AlertManager(
        model_name="plant-wgs-pipeline",
        environment="production",
    )
    alert_mgr.add_channel(ConsoleChannel())

    if slack_webhook:
        alert_mgr.add_channel(SlackChannel(webhook_url=slack_webhook))

    # Process all files
    results = []
    start_time = time.time()

    for i, fastq_path in enumerate(files, 1):
        print(f"\n[{i}/{len(files)}] ", end="")

        try:
            result = analyze_wgs_file(
                fastq_path,
                analyzer,
                max_reads=max_reads_per_file,
            )
            results.append(result)

            # Fire alert if low quality
            if not result["is_high_quality"]:
                alert_mgr.fire_alert(
                    alert_key=f"quality-{os.path.basename(fastq_path)}",
                    title="Low Quality WGS Sample",
                    description=f"Sample {os.path.basename(fastq_path)} failed quality checks",
                    primary_reason=result["plant_metrics"].quality_warnings[0] if result["plant_metrics"].quality_warnings else "Low quality",
                    affected_requests=1,
                    metrics={
                        "training_quality": result["plant_metrics"].training_data_quality,
                        "sequencing_quality": result["qual_stats"]["mean_quality"],
                        "q30_percent": result["qual_stats"]["q30_percent"],
                    },
                )

        except Exception as e:
            print(f"❌ Error processing {fastq_path}: {e}")
            results.append({
                "file": fastq_path,
                "verdict": "ERROR",
                "error": str(e),
                "is_high_quality": False,
            })

    # Generate summary report
    elapsed = time.time() - start_time

    print(f"\n{'='*80}")
    print("BATCH ANALYSIS SUMMARY")
    print(f"{'='*80}\n")

    green = sum(1 for r in results if r["verdict"] == "GREEN")
    yellow = sum(1 for r in results if r["verdict"] == "YELLOW")
    red = sum(1 for r in results if r["verdict"] == "RED")
    errors = sum(1 for r in results if r["verdict"] == "ERROR")

    print(f"Total Files: {len(results)}")
    print(f"✅ High Quality: {green} ({green/len(results)*100:.1f}%)")
    print(f"⚠️  Medium Quality: {yellow} ({yellow/len(results)*100:.1f}%)")
    print(f"❌ Low Quality: {red} ({red/len(results)*100:.1f}%)")
    if errors:
        print(f"⚠️  Errors: {errors}")

    print(f"\nProcessing Time: {elapsed:.1f} seconds ({elapsed/len(results):.1f}s per file)")

    # Detailed report to file
    with open(output_report, 'w') as f:
        f.write("="*80 + "\n")
        f.write("PLANT WGS QUALITY REPORT\n")
        f.write("="*80 + "\n\n")

        f.write(f"Total Samples: {len(results)}\n")
        f.write(f"High Quality: {green} ({green/len(results)*100:.1f}%)\n")
        f.write(f"Medium Quality: {yellow} ({yellow/len(results)*100:.1f}%)\n")
        f.write(f"Low Quality: {red} ({red/len(results)*100:.1f}%)\n\n")

        f.write("="*80 + "\n")
        f.write("DETAILED RESULTS\n")
        f.write("="*80 + "\n\n")

        for result in results:
            f.write(f"File: {os.path.basename(result['file'])}\n")
            f.write(f"Verdict: {result['verdict']}\n")

            if "plant_metrics" in result:
                pm = result["plant_metrics"]
                qs = result["qual_stats"]

                f.write(f"  Genome Size: {pm.genome_size_estimate/1e6:.1f} Mbp\n")
                f.write(f"  GC Content: {pm.genomic_metrics.gc_content:.2%}\n")
                f.write(f"  Sequencing Quality: Q{int(qs['mean_quality'])}\n")
                f.write(f"  Q30 %: {qs['q30_percent']:.1f}%\n")
                f.write(f"  Training Quality: {pm.training_data_quality:.2f}\n")

                if pm.quality_warnings:
                    f.write(f"  Warnings:\n")
                    for warning in pm.quality_warnings[:3]:
                        f.write(f"    - {warning}\n")

            f.write("\n")

    print(f"\n📄 Detailed report saved to: {output_report}")
    print(f"\n{'='*80}\n")

    return results


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Plant WGS Quality Monitor for FASTQ.GZ files"
    )
    parser.add_argument(
        "input",
        nargs="?",
        help="FASTQ or FASTQ.GZ file, or glob pattern for batch mode"
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Batch mode (process multiple files)"
    )
    parser.add_argument(
        "--max-reads",
        type=int,
        default=100000,
        help="Max reads per file (default: 100,000 for speed)"
    )
    parser.add_argument(
        "--output",
        default="wgs_quality_report.txt",
        help="Output report file (default: wgs_quality_report.txt)"
    )
    parser.add_argument(
        "--slack-webhook",
        help="Slack webhook URL for alerts"
    )

    args = parser.parse_args()

    if not args.input:
        parser.print_help()
        print("\nExamples:")
        print("  python monitor_fastq.py sample.fastq.gz")
        print("  python monitor_fastq.py --batch '/data/wgs/*.fastq.gz'")
        print("  python monitor_fastq.py --batch '/data/*.fastq.gz' --max-reads 50000")
        return

    # Initialize analyzer
    analyzer = PlantGenomicsAnalyzer()
    analyzer.EXPECTED_GENOME_SIZE = 850_000_000
    analyzer.EXPECTED_GC_CONTENT = 0.36

    if args.batch:
        # Batch mode
        batch_analyze(
            args.input,
            output_report=args.output,
            max_reads_per_file=args.max_reads,
            slack_webhook=args.slack_webhook,
        )
    else:
        # Single file mode
        result = analyze_wgs_file(
            args.input,
            analyzer,
            max_reads=args.max_reads,
        )


if __name__ == "__main__":
    main()
