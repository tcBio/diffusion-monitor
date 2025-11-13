"""
Plant WGS Quality Monitor for Windows
Analyzes FASTQ.GZ files on Windows systems

Usage:
    python monitor_fastq_windows.py F:\\wgs\\PRJNA734114\\sample.fastq.gz
    python monitor_fastq_windows.py --batch "F:\\wgs\\PRJNA734114\\*.fastq.gz"
"""

import sys
import os
import gzip
from typing import List, Tuple, Dict
from pathlib import Path
import glob

# Simplified version for Windows - no external dependencies on monitoring components
# This is a standalone script you can run on your Windows machine

class FASTQParser:
    """Parse FASTQ and FASTQ.GZ files"""

    @staticmethod
    def parse_fastq(file_path: str, max_reads: int = 100000) -> Tuple[str, List[int]]:
        """Parse FASTQ or FASTQ.GZ file"""
        is_gzipped = file_path.endswith('.gz')

        if is_gzipped:
            f = gzip.open(file_path, 'rt')
        else:
            f = open(file_path, 'r')

        sequences = []
        qualities = []

        try:
            read_count = 0
            while True:
                header = f.readline()
                if not header:
                    break

                sequence = f.readline().strip()
                plus = f.readline()
                quality = f.readline().strip()

                if not sequence or not quality:
                    break

                sequences.append(sequence)
                qual_scores = [ord(q) - 33 for q in quality]
                qualities.extend(qual_scores)

                read_count += 1
                if max_reads and read_count >= max_reads:
                    break

                if read_count % 10000 == 0:
                    print(f"  Processed {read_count:,} reads...", end='\r')

        finally:
            f.close()

        full_sequence = ''.join(sequences)
        print(f"\n  Loaded {read_count:,} reads, {len(full_sequence):,} bases")

        return full_sequence, qualities

    @staticmethod
    def calculate_quality_stats(quality_scores: List[int]) -> Dict:
        """Calculate quality statistics from Phred scores"""
        if not quality_scores:
            return {
                "mean_quality": 0.0,
                "q20_percent": 0.0,
                "q30_percent": 0.0,
            }

        mean_q = sum(quality_scores) / len(quality_scores)
        q20_count = sum(1 for q in quality_scores if q >= 20)
        q30_count = sum(1 for q in quality_scores if q >= 30)

        return {
            "mean_quality": mean_q,
            "q20_percent": q20_count / len(quality_scores) * 100,
            "q30_percent": q30_count / len(quality_scores) * 100,
        }


def calculate_gc_content(sequence: str) -> float:
    """Calculate GC content"""
    gc_count = sequence.count('G') + sequence.count('C')
    total = len([b for b in sequence if b in 'ACGT'])
    return gc_count / total if total > 0 else 0.0


def calculate_complexity(sequence: str) -> float:
    """Calculate sequence complexity"""
    if len(sequence) < 3:
        return 0.0

    k = 3
    kmers = [sequence[i:i+k] for i in range(len(sequence) - k + 1)]
    unique_kmers = len(set(kmers))
    total_kmers = len(kmers)

    return unique_kmers / total_kmers if total_kmers > 0 else 0.0


def find_longest_homopolymer(sequence: str) -> int:
    """Find longest homopolymer run"""
    max_length = 0
    current_length = 1

    for i in range(1, len(sequence)):
        if sequence[i] == sequence[i-1]:
            current_length += 1
            max_length = max(max_length, current_length)
        else:
            current_length = 1

    return max_length


def analyze_fastq_file(fastq_path: str, max_reads: int = 100000) -> Dict:
    """Analyze a single FASTQ.GZ file"""

    print(f"\n{'='*80}")
    print(f"Analyzing: {os.path.basename(fastq_path)}")
    print(f"{'='*80}")

    # Parse FASTQ
    print("Loading FASTQ data...")
    sequence, quality_scores = FASTQParser.parse_fastq(fastq_path, max_reads)

    # Calculate quality stats
    qual_stats = FASTQParser.calculate_quality_stats(quality_scores)

    print(f"\nSequencing Quality:")
    print(f"  Mean Quality: Q{int(qual_stats['mean_quality'])}")
    print(f"  Q20 bases: {qual_stats['q20_percent']:.1f}%")
    print(f"  Q30 bases: {qual_stats['q30_percent']:.1f}%")

    # Calculate genomic metrics
    print(f"\nAnalyzing genomic content...")

    gc_content = calculate_gc_content(sequence)
    complexity = calculate_complexity(sequence)
    homopolymer = find_longest_homopolymer(sequence)
    n_content = sequence.count('N') / len(sequence) if len(sequence) > 0 else 0

    # Print results
    print(f"\n{'─'*80}")
    print("GENOMIC ANALYSIS RESULTS")
    print(f"{'─'*80}")

    print(f"\n📊 Sequence Composition:")
    print(f"  Genome Size: {len(sequence):,} bp ({len(sequence)/1e6:.1f} Mbp)")
    print(f"  GC Content: {gc_content:.2%}")
    print(f"  Complexity Score: {complexity:.2f}")
    print(f"  Max Homopolymer: {homopolymer} bases")
    print(f"  N-content: {n_content:.2%}")

    # Quality assessment
    print(f"\n⭐ Quality Scores:")
    print(f"  Sequencing Quality: Q{int(qual_stats['mean_quality'])}")
    print(f"  Q30 Percentage: {qual_stats['q30_percent']:.1f}%")

    # Determine verdict
    is_high_qual = (
        qual_stats['q30_percent'] > 80 and
        0.35 < gc_content < 0.40 and
        complexity > 0.6 and
        homopolymer < 50
    )

    print(f"\n{'─'*80}")

    if is_high_qual:
        verdict = "✅ HIGH QUALITY - Suitable for analysis"
    elif qual_stats['q30_percent'] > 60:
        verdict = "⚠️  MEDIUM QUALITY - Review recommended"
    else:
        verdict = "❌ LOW QUALITY - Do not use"

    print(f"\n🎯 VERDICT: {verdict}")

    # Warnings
    warnings = []
    if qual_stats['q30_percent'] < 80:
        warnings.append(f"Low sequencing quality: {qual_stats['q30_percent']:.1f}% Q30 (expected >80%)")
    if gc_content < 0.35 or gc_content > 0.40:
        warnings.append(f"GC content {gc_content:.2%} outside expected range (35-40%)")
    if complexity < 0.6:
        warnings.append(f"Low sequence complexity: {complexity:.2f}")
    if homopolymer > 20:
        warnings.append(f"Long homopolymer run: {homopolymer} bases")

    if warnings:
        print(f"\n⚠️  WARNINGS:")
        for warning in warnings:
            print(f"  - {warning}")

    print(f"\n{'='*80}\n")

    return {
        "file": fastq_path,
        "verdict": verdict,
        "q30_percent": qual_stats['q30_percent'],
        "gc_content": gc_content,
        "is_high_quality": is_high_qual,
    }


def batch_analyze(file_pattern: str, output_report: str = "wgs_quality_report.txt"):
    """Analyze multiple FASTQ.GZ files"""

    # Find files
    files = glob.glob(file_pattern)
    print(f"\n🔍 Found {len(files)} FASTQ files to analyze\n")

    if not files:
        print(f"❌ No files found matching: {file_pattern}")
        return

    # Process all files
    results = []

    for i, fastq_path in enumerate(files, 1):
        print(f"\n[{i}/{len(files)}] ", end="")

        try:
            result = analyze_fastq_file(fastq_path)
            results.append(result)
        except Exception as e:
            print(f"❌ Error processing {fastq_path}: {e}")
            results.append({
                "file": fastq_path,
                "verdict": "ERROR",
                "error": str(e),
                "is_high_quality": False,
            })

    # Generate summary
    print(f"\n{'='*80}")
    print("BATCH ANALYSIS SUMMARY")
    print(f"{'='*80}\n")

    high = sum(1 for r in results if "HIGH" in r["verdict"])
    medium = sum(1 for r in results if "MEDIUM" in r["verdict"])
    low = sum(1 for r in results if "LOW" in r["verdict"])
    errors = sum(1 for r in results if "ERROR" in r["verdict"])

    print(f"Total Files: {len(results)}")
    print(f"✅ High Quality: {high} ({high/len(results)*100:.1f}%)")
    print(f"⚠️  Medium Quality: {medium} ({medium/len(results)*100:.1f}%)")
    print(f"❌ Low Quality: {low} ({low/len(results)*100:.1f}%)")
    if errors:
        print(f"⚠️  Errors: {errors}")

    # Save report
    with open(output_report, 'w') as f:
        f.write("="*80 + "\n")
        f.write("PLANT WGS QUALITY REPORT\n")
        f.write("="*80 + "\n\n")

        f.write(f"Total Samples: {len(results)}\n")
        f.write(f"High Quality: {high} ({high/len(results)*100:.1f}%)\n")
        f.write(f"Medium Quality: {medium} ({medium/len(results)*100:.1f}%)\n")
        f.write(f"Low Quality: {low} ({low/len(results)*100:.1f}%)\n\n")

        f.write("="*80 + "\n")
        f.write("DETAILED RESULTS\n")
        f.write("="*80 + "\n\n")

        for result in results:
            f.write(f"File: {os.path.basename(result['file'])}\n")
            f.write(f"Verdict: {result['verdict']}\n")

            if "q30_percent" in result:
                f.write(f"  Q30: {result['q30_percent']:.1f}%\n")
                f.write(f"  GC: {result['gc_content']:.2%}\n")

            f.write("\n")

    print(f"\n📄 Detailed report saved to: {output_report}")
    print(f"\n{'='*80}\n")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Plant WGS Quality Monitor for Windows"
    )
    parser.add_argument(
        "input",
        nargs="?",
        help="FASTQ.GZ file or pattern for batch mode"
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
        help="Max reads per file (default: 100,000)"
    )
    parser.add_argument(
        "--output",
        default="wgs_quality_report.txt",
        help="Output report file"
    )

    args = parser.parse_args()

    if not args.input:
        parser.print_help()
        print("\nExamples:")
        print('  python monitor_fastq_windows.py "F:\\wgs\\PRJNA734114\\sample.fastq.gz"')
        print('  python monitor_fastq_windows.py --batch "F:\\wgs\\PRJNA734114\\*.fastq.gz"')
        return

    if args.batch:
        batch_analyze(args.input, output_report=args.output)
    else:
        analyze_fastq_file(args.input, max_reads=args.max_reads)


if __name__ == "__main__":
    main()
