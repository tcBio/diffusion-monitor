"""
Plant Genomics Monitoring

Specialized monitoring for plant WGS (Whole Genome Sequencing) data
and in silico methods generating large-scale genomic datasets.

Features:
- Plant-specific quality metrics
- Secondary_Metabolite/terpene gene detection
- Strain identification and validation
- WGS quality control (coverage, mapping, variants)
- Dataset quality monitoring for ML/AI applications

Author: Brian Worthington
"""

from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
import numpy as np
from .genomic_metrics import GenomicQualityAnalyzer, GenomicQualityMetrics


@dataclass
class PlantGenomicMetrics:
    """Plant-specific genomic quality metrics"""

    # Basic genomic metrics
    genomic_metrics: GenomicQualityMetrics

    # Plant-specific composition
    genome_size_estimate: int           # Estimated genome size (bp)
    heterozygosity_rate: float          # SNP density (variants per kb)
    repeat_content: float               # Repetitive element fraction

    # Secondary_Metabolite biosynthesis genes
    thca_synthase_detected: bool        # Metabolite-A synthase gene
    cbda_synthase_detected: bool        # Metabolite-B synthase gene
    cbga_synthase_detected: bool        # Metabolite-C synthase gene
    secondary_metabolite_gene_count: int         # Total secondary_metabolite genes

    # Terpene biosynthesis
    terpene_synthase_count: int         # Terpene synthase genes
    myrcene_synthase_detected: bool     # Major terpene
    limonene_synthase_detected: bool    # Major terpene

    # Dataset quality (for ML) - required fields
    sequence_completeness: float        # Fraction of complete sequences
    training_data_quality: float        # Overall quality score for ML (0-1)

    # Overall assessment - required fields
    is_valid_plant_genome: bool
    quality_warnings: List[str]

    # Sex determination - optional fields
    predicted_sex: Optional[str] = None  # "XX" (female), "XY" (male), or "Unknown"
    sex_chromosome_coverage: Optional[float] = None

    # WGS Quality (if applicable) - optional fields
    mean_coverage: Optional[float] = None      # Mean sequencing depth
    coverage_uniformity: Optional[float] = None # Coverage variance
    mapping_quality: Optional[float] = None     # Mean MAPQ
    variant_quality: Optional[float] = None     # Mean variant quality

    # Strain characteristics - optional fields
    chemotype_prediction: Optional[str] = None   # Type I (Met-A), II (mixed), III (Met-B)
    strain_similarity: Optional[float] = None    # Similarity to reference strains


class PlantGenomicsAnalyzer:
    """
    Analyzer for plant WGS data and in silico generated datasets

    Supports:
    - Quality control for WGS data
    - Plant-specific gene detection
    - Strain characterization
    - Dataset validation for ML/AI training
    """

    # Plant-specific gene signatures (simplified - production would use full sequences)
    CANNABINOID_GENE_SIGNATURES = {
        "Metabolite-AS": ["Metabolite-AS", "Metabolite-A_SYNTHASE", "Met-A_SYNTHASE"],
        "Metabolite-BS": ["Metabolite-BS", "Metabolite-B_SYNTHASE", "Met-B_SYNTHASE"],
        "Metabolite-CS": ["Metabolite-CS", "Metabolite-C_SYNTHASE"],
    }

    TERPENE_SYNTHASE_SIGNATURES = {
        "MYRCENE": ["MYR", "MYRCENE_SYNTHASE"],
        "LIMONENE": ["LIM", "LIMONENE_SYNTHASE"],
    }

    # Plant genome characteristics
    EXPECTED_GENOME_SIZE = 900_000_000  # ~900 Mbp
    EXPECTED_HETEROZYGOSITY = 0.003     # ~3 SNPs per kb
    EXPECTED_GC_CONTENT = 0.38          # ~38% GC for plant

    def __init__(
        self,
        reference_strains: Optional[Dict[str, str]] = None,
        expected_coverage: float = 30.0,
        min_mapping_quality: float = 30.0,
    ):
        """
        Initialize plant genomics analyzer

        Args:
            reference_strains: Dict of strain name -> reference sequence
            expected_coverage: Expected WGS coverage (default: 30X)
            min_mapping_quality: Minimum acceptable MAPQ
        """
        self.reference_strains = reference_strains or {}
        self.expected_coverage = expected_coverage
        self.min_mapping_quality = min_mapping_quality

        # Base genomic analyzer (DNA-specific)
        self.genomic_analyzer = GenomicQualityAnalyzer(
            sequence_type="dna",
            expected_gc_content=self.EXPECTED_GC_CONTENT,
            gc_tolerance=0.05,  # Stricter for plant
            max_homopolymer_length=15,
            min_complexity=0.25,
        )

    def analyze_plant_sequence(
        self,
        sequence: str,
        annotations: Optional[Dict] = None,
        wgs_metrics: Optional[Dict] = None,
    ) -> PlantGenomicMetrics:
        """
        Analyze a plant genomic sequence

        Args:
            sequence: DNA sequence
            annotations: Optional gene annotations dict
            wgs_metrics: Optional WGS quality metrics dict
                {
                    "coverage": float,
                    "mapping_quality": float,
                    "heterozygosity": float,
                    "variants": List[Dict],
                }

        Returns:
            PlantGenomicMetrics object
        """
        # Basic genomic analysis
        genomic_metrics = self.genomic_analyzer.analyze_sequence(sequence)

        # Estimate genome size
        genome_size = len(sequence)

        # Calculate heterozygosity (if WGS metrics provided)
        heterozygosity = 0.0
        if wgs_metrics and "heterozygosity" in wgs_metrics:
            heterozygosity = wgs_metrics["heterozygosity"]
        else:
            # Estimate from N-content (simplification)
            heterozygosity = genomic_metrics.n_content * 0.01

        # Estimate repeat content (simplified)
        repeat_content = 1.0 - genomic_metrics.complexity_score

        # Detect secondary_metabolite genes
        secondary_metabolite_genes = self._detect_secondary_metabolite_genes(sequence, annotations)
        thca_detected = secondary_metabolite_genes["Metabolite-AS"]
        cbda_detected = secondary_metabolite_genes["Metabolite-BS"]
        cbga_detected = secondary_metabolite_genes["Metabolite-CS"]
        secondary_metabolite_count = sum(secondary_metabolite_genes.values())

        # Detect terpene synthases
        terpene_genes = self._detect_terpene_genes(sequence, annotations)
        myrcene_detected = terpene_genes["MYRCENE"]
        limonene_detected = terpene_genes["LIMONENE"]
        terpene_count = sum(terpene_genes.values())

        # Predict sex (simplified - would need Y chromosome markers)
        predicted_sex = self._predict_sex(sequence, annotations)

        # WGS quality metrics
        mean_coverage = None
        coverage_uniformity = None
        mapping_quality = None
        variant_quality = None

        if wgs_metrics:
            mean_coverage = wgs_metrics.get("coverage")
            mapping_quality = wgs_metrics.get("mapping_quality")
            if "coverage_variance" in wgs_metrics:
                coverage_uniformity = 1.0 - wgs_metrics["coverage_variance"]
            if "variants" in wgs_metrics:
                variant_quality = np.mean([v.get("quality", 0) for v in wgs_metrics["variants"]])

        # Predict chemotype
        chemotype = self._predict_chemotype(thca_detected, cbda_detected)

        # Calculate strain similarity (if references provided)
        strain_similarity = None
        if self.reference_strains:
            strain_similarity = self._calculate_strain_similarity(sequence)

        # Sequence completeness (based on N-content and genome size)
        completeness = (1.0 - genomic_metrics.n_content) * (
            min(1.0, genome_size / self.EXPECTED_GENOME_SIZE)
        )

        # Training data quality score
        training_quality = self._calculate_training_quality(
            genomic_metrics,
            secondary_metabolite_count,
            terpene_count,
            completeness,
            heterozygosity,
        )

        # Validation
        is_valid, warnings = self._validate_plant_genome(
            genomic_metrics,
            genome_size,
            heterozygosity,
            secondary_metabolite_count,
            mean_coverage,
            mapping_quality,
        )

        return PlantGenomicMetrics(
            genomic_metrics=genomic_metrics,
            genome_size_estimate=genome_size,
            heterozygosity_rate=heterozygosity,
            repeat_content=repeat_content,
            thca_synthase_detected=thca_detected,
            cbda_synthase_detected=cbda_detected,
            cbga_synthase_detected=cbga_detected,
            secondary_metabolite_gene_count=secondary_metabolite_count,
            terpene_synthase_count=terpene_count,
            myrcene_synthase_detected=myrcene_detected,
            limonene_synthase_detected=limonene_detected,
            predicted_sex=predicted_sex,
            sex_chromosome_coverage=None,
            mean_coverage=mean_coverage,
            coverage_uniformity=coverage_uniformity,
            mapping_quality=mapping_quality,
            variant_quality=variant_quality,
            chemotype_prediction=chemotype,
            strain_similarity=strain_similarity,
            sequence_completeness=completeness,
            training_data_quality=training_quality,
            is_valid_plant_genome=is_valid,
            quality_warnings=warnings,
        )

    def _detect_secondary_metabolite_genes(
        self,
        sequence: str,
        annotations: Optional[Dict],
    ) -> Dict[str, bool]:
        """Detect secondary_metabolite biosynthesis genes"""

        if annotations and "genes" in annotations:
            # Use provided annotations
            genes = [g.upper() for g in annotations["genes"]]
            return {
                "Metabolite-AS": any(sig in " ".join(genes) for sig in self.CANNABINOID_GENE_SIGNATURES["Metabolite-AS"]),
                "Metabolite-BS": any(sig in " ".join(genes) for sig in self.CANNABINOID_GENE_SIGNATURES["Metabolite-BS"]),
                "Metabolite-CS": any(sig in " ".join(genes) for sig in self.CANNABINOID_GENE_SIGNATURES["Metabolite-CS"]),
            }

        # Simplified: Look for signature sequences (in production, use BLAST)
        # For demo purposes, we'll assume presence based on sequence characteristics
        # In real implementation, would search for actual gene sequences
        return {
            "Metabolite-AS": len(sequence) > 100000,  # Placeholder
            "Metabolite-BS": len(sequence) > 100000,
            "Metabolite-CS": len(sequence) > 100000,
        }

    def _detect_terpene_genes(
        self,
        sequence: str,
        annotations: Optional[Dict],
    ) -> Dict[str, bool]:
        """Detect terpene synthase genes"""

        if annotations and "genes" in annotations:
            genes = [g.upper() for g in annotations["genes"]]
            return {
                "MYRCENE": any(sig in " ".join(genes) for sig in self.TERPENE_SYNTHASE_SIGNATURES["MYRCENE"]),
                "LIMONENE": any(sig in " ".join(genes) for sig in self.TERPENE_SYNTHASE_SIGNATURES["LIMONENE"]),
            }

        # Placeholder for demo
        return {
            "MYRCENE": len(sequence) > 50000,
            "LIMONENE": len(sequence) > 50000,
        }

    def _predict_sex(
        self,
        sequence: str,
        annotations: Optional[Dict],
    ) -> str:
        """Predict plant sex from genomic data"""

        if annotations and "sex" in annotations:
            return annotations["sex"]

        # In production, would look for Y chromosome markers
        # For now, return Unknown
        return "Unknown"

    def _predict_chemotype(
        self,
        has_thca: bool,
        has_cbda: bool,
    ) -> str:
        """
        Predict chemotype based on secondary_metabolite genes

        - Type I: Met-A-dominant (recreational)
        - Type II: Mixed Met-A/Met-B
        - Type III: Met-B-dominant (hemp)
        """
        if has_thca and not has_cbda:
            return "Type I (Met-A-dominant)"
        elif has_cbda and not has_thca:
            return "Type III (Met-B-dominant)"
        elif has_thca and has_cbda:
            return "Type II (Mixed)"
        else:
            return "Unknown"

    def _calculate_strain_similarity(self, sequence: str) -> float:
        """Calculate similarity to known strains"""
        # In production, would use alignment tools
        # For now, return placeholder
        return 0.85  # 85% similar to reference

    def _calculate_training_quality(
        self,
        genomic_metrics: GenomicQualityMetrics,
        secondary_metabolite_count: int,
        terpene_count: int,
        completeness: float,
        heterozygosity: float,
    ) -> float:
        """
        Calculate overall quality score for ML training data

        Factors:
        - Genomic validity (30%)
        - Gene completeness (25%)
        - Sequence completeness (25%)
        - Heterozygosity (20%)
        """
        score = 0.0

        # Genomic validity
        score += 0.30 * genomic_metrics.biological_validity_score

        # Gene completeness (expect at least 3 secondary_metabolite genes)
        gene_score = min(1.0, (secondary_metabolite_count + terpene_count) / 5.0)
        score += 0.25 * gene_score

        # Sequence completeness
        score += 0.25 * completeness

        # Heterozygosity (should be near expected)
        het_score = 1.0 - abs(heterozygosity - self.EXPECTED_HETEROZYGOSITY) / self.EXPECTED_HETEROZYGOSITY
        het_score = max(0, min(1.0, het_score))
        score += 0.20 * het_score

        return score

    def _validate_plant_genome(
        self,
        genomic_metrics: GenomicQualityMetrics,
        genome_size: int,
        heterozygosity: float,
        secondary_metabolite_count: int,
        mean_coverage: Optional[float],
        mapping_quality: Optional[float],
    ) -> Tuple[bool, List[str]]:
        """Validate plant genome and generate warnings"""

        warnings = []
        is_valid = True

        # Check genome size
        if genome_size < 500_000_000:  # Less than 500 Mbp
            warnings.append(f"Genome size too small: {genome_size/1e6:.1f} Mbp (expected ~900 Mbp)")
            is_valid = False

        # Check GC content
        if genomic_metrics.gc_deviation > 0.05:
            warnings.append(
                f"GC content {genomic_metrics.gc_content:.2%} deviates from expected "
                f"{self.EXPECTED_GC_CONTENT:.2%}"
            )

        # Check heterozygosity
        if heterozygosity > self.EXPECTED_HETEROZYGOSITY * 3:
            warnings.append(f"Unusually high heterozygosity: {heterozygosity:.4f}")

        # Check secondary_metabolite genes
        if secondary_metabolite_count == 0:
            warnings.append("No secondary_metabolite biosynthesis genes detected")
            is_valid = False

        # Check WGS quality
        if mean_coverage is not None:
            if mean_coverage < self.expected_coverage * 0.5:
                warnings.append(f"Low coverage: {mean_coverage:.1f}X (expected >{self.expected_coverage}X)")
                is_valid = False

        if mapping_quality is not None:
            if mapping_quality < self.min_mapping_quality:
                warnings.append(f"Low mapping quality: {mapping_quality:.1f} (expected >{self.min_mapping_quality})")

        # Check basic genomic validity
        if not genomic_metrics.is_biologically_valid:
            warnings.append("Failed basic genomic validity checks")
            is_valid = False

        return is_valid, warnings


def create_plant_quality_detector():
    """
    Create a pre-configured quality detector for plant genomics

    Returns tuple of (quality_detector, genomic_analyzer, alert_manager)
    """
    from .quality_detector import QualityDetector
    from .alert_manager import AlertManager, ConsoleChannel

    # Standard diffusion quality detector
    quality_detector = QualityDetector(
        baseline_window=100,
        alert_threshold=3,
        confidence_threshold=2.0,
    )

    # Plant-specific analyzer
    genomic_analyzer = PlantGenomicsAnalyzer(
        expected_coverage=30.0,
        min_mapping_quality=30.0,
    )

    # Alert manager
    alert_mgr = AlertManager(
        model_name="plant-wgs-generator",
        environment="production",
    )
    alert_mgr.add_channel(ConsoleChannel())

    return quality_detector, genomic_analyzer, alert_mgr
