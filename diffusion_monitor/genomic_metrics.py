"""
Genomic-Specific Metrics for Diffusion Model Monitoring

Extends the base quality detector with domain-specific metrics for:
- DNA/RNA sequence generation
- Protein structure prediction
- Gene expression modeling
- General biomolecular generation

Author: Brian Worthington
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np
from collections import Counter


@dataclass
class GenomicQualityMetrics:
    """Genomic-specific quality metrics"""

    # Sequence composition
    gc_content: float                    # GC content (0-1)
    gc_deviation: float                  # Deviation from expected
    homopolymer_max_length: int         # Longest homopolymer run
    complexity_score: float              # Sequence complexity (0-1)

    # Biological validity
    has_valid_start_codon: bool         # ATG present
    has_valid_stop_codon: bool          # TAA/TAG/TGA present
    orf_count: int                      # Number of ORFs detected
    n_content: float                    # Ambiguous base content

    # Quality scores
    mean_quality: float                 # Average quality score (if available)
    low_quality_regions: int            # Number of low-quality regions

    # Overall quality (required fields)
    biological_validity_score: float    # 0-1, overall validity
    is_biologically_valid: bool         # Pass/fail threshold

    # Structural metrics (for proteins) - optional fields
    predicted_disorder: Optional[float] = None  # Disorder score
    hydrophobic_ratio: Optional[float] = None   # Hydrophobic residue ratio

    # Comparative metrics - optional fields
    similarity_to_reference: Optional[float] = None  # BLAST/alignment score
    novelty_score: Optional[float] = None            # How novel vs database


class GenomicQualityAnalyzer:
    """
    Analyzes genomic sequences for quality and biological validity

    Supports:
    - DNA sequences (ACGT)
    - RNA sequences (ACGU)
    - Protein sequences (20 amino acids)
    - Quality scores (Phred scores)
    """

    def __init__(
        self,
        sequence_type: str = "dna",  # "dna", "rna", "protein"
        expected_gc_content: float = 0.50,
        gc_tolerance: float = 0.10,
        max_homopolymer_length: int = 10,
        min_complexity: float = 0.30,
    ):
        """
        Initialize genomic analyzer

        Args:
            sequence_type: Type of sequence ("dna", "rna", "protein")
            expected_gc_content: Expected GC content (0-1)
            gc_tolerance: Acceptable GC deviation
            max_homopolymer_length: Max acceptable homopolymer length
            min_complexity: Minimum sequence complexity
        """
        self.sequence_type = sequence_type.lower()
        self.expected_gc_content = expected_gc_content
        self.gc_tolerance = gc_tolerance
        self.max_homopolymer_length = max_homopolymer_length
        self.min_complexity = min_complexity

        # Define valid bases
        self.valid_bases = {
            "dna": set("ACGT"),
            "rna": set("ACGU"),
            "protein": set("ACDEFGHIKLMNPQRSTVWY"),
        }

        # Codon tables
        self.start_codons = {"ATG"}
        self.stop_codons = {"TAA", "TAG", "TGA"}

        # Hydrophobic amino acids
        self.hydrophobic_aa = set("AILMFWV")

    def analyze_sequence(
        self,
        sequence: str,
        quality_scores: Optional[List[int]] = None,
        reference_sequence: Optional[str] = None,
    ) -> GenomicQualityMetrics:
        """
        Analyze a genomic sequence for quality and validity

        Args:
            sequence: The generated sequence (DNA/RNA/protein)
            quality_scores: Optional Phred quality scores
            reference_sequence: Optional reference for comparison

        Returns:
            GenomicQualityMetrics object
        """
        sequence = sequence.upper().strip()

        # Basic composition
        gc_content = self._calculate_gc_content(sequence)
        gc_deviation = abs(gc_content - self.expected_gc_content)

        # Homopolymer detection
        homopolymer_length = self._detect_longest_homopolymer(sequence)

        # Complexity
        complexity = self._calculate_complexity(sequence)

        # N-content (ambiguous bases)
        n_content = sequence.count('N') / len(sequence) if len(sequence) > 0 else 0

        # Biological validity (DNA/RNA specific)
        has_start, has_stop, orf_count = False, False, 0
        if self.sequence_type in ["dna", "rna"]:
            has_start = self._has_start_codon(sequence)
            has_stop = self._has_stop_codon(sequence)
            orf_count = self._count_orfs(sequence)

        # Quality scores
        mean_quality = 0.0
        low_quality_regions = 0
        if quality_scores:
            mean_quality = np.mean(quality_scores)
            low_quality_regions = sum(1 for q in quality_scores if q < 20)

        # Protein-specific metrics
        predicted_disorder = None
        hydrophobic_ratio = None
        if self.sequence_type == "protein":
            hydrophobic_ratio = self._calculate_hydrophobic_ratio(sequence)
            # Disorder prediction would need a model; placeholder for now
            predicted_disorder = 0.0

        # Comparative metrics
        similarity = None
        if reference_sequence:
            similarity = self._calculate_similarity(sequence, reference_sequence)

        # Overall biological validity score
        validity_score = self._calculate_validity_score(
            gc_deviation, homopolymer_length, complexity, n_content,
            has_start, has_stop, orf_count
        )

        is_valid = validity_score > 0.7  # Threshold

        return GenomicQualityMetrics(
            gc_content=gc_content,
            gc_deviation=gc_deviation,
            homopolymer_max_length=homopolymer_length,
            complexity_score=complexity,
            has_valid_start_codon=has_start,
            has_valid_stop_codon=has_stop,
            orf_count=orf_count,
            n_content=n_content,
            mean_quality=mean_quality,
            low_quality_regions=low_quality_regions,
            predicted_disorder=predicted_disorder,
            hydrophobic_ratio=hydrophobic_ratio,
            similarity_to_reference=similarity,
            novelty_score=1.0 - similarity if similarity else None,
            biological_validity_score=validity_score,
            is_biologically_valid=is_valid,
        )

    def _calculate_gc_content(self, sequence: str) -> float:
        """Calculate GC content"""
        if self.sequence_type == "protein":
            return 0.0  # Not applicable

        gc_count = sequence.count('G') + sequence.count('C')
        total = len([b for b in sequence if b in self.valid_bases[self.sequence_type]])

        return gc_count / total if total > 0 else 0.0

    def _detect_longest_homopolymer(self, sequence: str) -> int:
        """Find longest homopolymer run (AAAA, TTTT, etc.)"""
        max_length = 0
        current_length = 1

        for i in range(1, len(sequence)):
            if sequence[i] == sequence[i-1]:
                current_length += 1
                max_length = max(max_length, current_length)
            else:
                current_length = 1

        return max_length

    def _calculate_complexity(self, sequence: str) -> float:
        """
        Calculate sequence complexity (0-1)
        Low complexity = repetitive (AAAAAAA)
        High complexity = diverse (ACGTACGT)
        """
        if len(sequence) < 2:
            return 0.0

        # Count unique k-mers (k=3)
        k = 3
        kmers = [sequence[i:i+k] for i in range(len(sequence) - k + 1)]
        unique_kmers = len(set(kmers))
        total_kmers = len(kmers)

        return unique_kmers / total_kmers if total_kmers > 0 else 0.0

    def _has_start_codon(self, sequence: str) -> bool:
        """Check if sequence has start codon (ATG)"""
        return any(sequence[i:i+3] in self.start_codons
                  for i in range(len(sequence) - 2))

    def _has_stop_codon(self, sequence: str) -> bool:
        """Check if sequence has stop codon"""
        return any(sequence[i:i+3] in self.stop_codons
                  for i in range(len(sequence) - 2))

    def _count_orfs(self, sequence: str) -> int:
        """Count Open Reading Frames (ORFs)"""
        orf_count = 0

        # Check all three reading frames
        for frame in range(3):
            in_orf = False
            orf_start = -1

            for i in range(frame, len(sequence) - 2, 3):
                codon = sequence[i:i+3]

                if codon in self.start_codons and not in_orf:
                    in_orf = True
                    orf_start = i

                elif codon in self.stop_codons and in_orf:
                    # Check minimum ORF length (30 codons = 90 bp)
                    if (i - orf_start) >= 90:
                        orf_count += 1
                    in_orf = False

        return orf_count

    def _calculate_hydrophobic_ratio(self, sequence: str) -> float:
        """Calculate ratio of hydrophobic amino acids"""
        if self.sequence_type != "protein":
            return 0.0

        hydrophobic_count = sum(1 for aa in sequence if aa in self.hydrophobic_aa)
        return hydrophobic_count / len(sequence) if len(sequence) > 0 else 0.0

    def _calculate_similarity(self, sequence: str, reference: str) -> float:
        """
        Calculate sequence similarity (simple alignment)
        For production, use BLAST or proper alignment tools
        """
        # Simple edit distance-based similarity
        min_len = min(len(sequence), len(reference))
        if min_len == 0:
            return 0.0

        matches = sum(1 for i in range(min_len) if sequence[i] == reference[i])
        return matches / min_len

    def _calculate_validity_score(
        self,
        gc_deviation: float,
        homopolymer_length: int,
        complexity: float,
        n_content: float,
        has_start: bool,
        has_stop: bool,
        orf_count: int,
    ) -> float:
        """
        Calculate overall biological validity score (0-1)

        Weights different quality factors
        """
        score = 0.0

        # GC content (20%)
        gc_score = max(0, 1 - (gc_deviation / self.gc_tolerance))
        score += 0.20 * gc_score

        # Homopolymer (15%)
        homopolymer_score = 1.0 if homopolymer_length <= self.max_homopolymer_length else 0.0
        score += 0.15 * homopolymer_score

        # Complexity (20%)
        complexity_score = max(0, (complexity - self.min_complexity) / (1 - self.min_complexity))
        score += 0.20 * complexity_score

        # N-content (15%)
        n_score = max(0, 1 - n_content * 10)  # Penalize N's heavily
        score += 0.15 * n_score

        # ORF presence (30% for DNA/RNA, distributed otherwise)
        if self.sequence_type in ["dna", "rna"]:
            orf_score = 0.0
            if has_start:
                orf_score += 0.10
            if has_stop:
                orf_score += 0.10
            if orf_count > 0:
                orf_score += 0.10
            score += orf_score
        else:
            # Protein: distribute to other metrics
            score += 0.30 * complexity_score

        return min(1.0, max(0.0, score))

    def check_biological_anomalies(
        self,
        metrics: GenomicQualityMetrics
    ) -> List[str]:
        """
        Check for biological anomalies and return warnings

        Returns list of warning messages
        """
        warnings = []

        # GC content
        if metrics.gc_deviation > self.gc_tolerance:
            warnings.append(
                f"GC content {metrics.gc_content:.2%} deviates from expected "
                f"{self.expected_gc_content:.2%} by {metrics.gc_deviation:.2%}"
            )

        # Homopolymer
        if metrics.homopolymer_max_length > self.max_homopolymer_length:
            warnings.append(
                f"Long homopolymer run detected: {metrics.homopolymer_max_length} bases"
            )

        # Complexity
        if metrics.complexity_score < self.min_complexity:
            warnings.append(
                f"Low sequence complexity: {metrics.complexity_score:.2f}"
            )

        # N-content
        if metrics.n_content > 0.01:  # >1% N's
            warnings.append(
                f"High ambiguous base content: {metrics.n_content:.2%}"
            )

        # ORFs (DNA/RNA)
        if self.sequence_type in ["dna", "rna"]:
            if not metrics.has_valid_start_codon:
                warnings.append("No start codon (ATG) detected")
            if not metrics.has_valid_stop_codon:
                warnings.append("No stop codon detected")
            if metrics.orf_count == 0:
                warnings.append("No valid ORFs detected")

        # Overall validity
        if not metrics.is_biologically_valid:
            warnings.append(
                f"Overall biological validity score low: "
                f"{metrics.biological_validity_score:.2f}"
            )

        return warnings


def integrate_with_quality_detector(
    diffusion_metrics: Dict,
    sequence: str,
    analyzer: GenomicQualityAnalyzer,
) -> Dict:
    """
    Integrate genomic metrics with diffusion quality metrics

    Combines standard diffusion quality (confidence, perplexity) with
    genomic-specific metrics (GC content, ORFs, etc.)

    Args:
        diffusion_metrics: Standard diffusion metrics dict
        sequence: Generated genomic sequence
        analyzer: GenomicQualityAnalyzer instance

    Returns:
        Combined metrics dict
    """
    # Analyze genomic sequence
    genomic_metrics = analyzer.analyze_sequence(sequence)

    # Check for anomalies
    warnings = analyzer.check_biological_anomalies(genomic_metrics)

    # Combine metrics
    combined = {
        **diffusion_metrics,
        "genomic_gc_content": genomic_metrics.gc_content,
        "genomic_complexity": genomic_metrics.complexity_score,
        "genomic_validity_score": genomic_metrics.biological_validity_score,
        "genomic_is_valid": genomic_metrics.is_biologically_valid,
        "genomic_warnings": warnings,
        "genomic_orf_count": genomic_metrics.orf_count,
        "genomic_homopolymer_length": genomic_metrics.homopolymer_max_length,
    }

    return combined
