# Understanding FASTQ.GZ Files - Your WGS Data

## 🧬 What's in Your FASTQ.GZ Files?

Your plant WGS files contain **two critical pieces of information**:

### 1. **The Sequence** (What we had in FASTA)
```
ATCGATCGATCG...
```

### 2. **Quality Scores** (NEW! Only in FASTQ)
```
IIIIIIHHHGGG...
```
Each letter represents the **confidence** that the base is correct.

---

## 📄 FASTQ Format Explained

### **Raw FASTQ File Structure** (4 lines per read):

```
@SEQ_ID                          ← Line 1: Header (starts with @)
GATTTGGGGTTCAAAGCAGTATCGATCAA   ← Line 2: DNA Sequence
+                                ← Line 3: Separator (just +)
!''*((((***+))%%%++)(%%%%).1   ← Line 4: Quality Scores
```

**Repeats for millions of reads...**

### **What Each Line Means:**

**Line 1 - Header:**
```
@M01234:123:000000000-A1234:1:1101:15000:1234 1:N:0:1
│       │   │                  │ │    │     │    │││││
│       │   │                  │ │    │     │    └┴┴┴┴─ Other metadata
│       │   │                  │ │    │     └────────── Read number
│       │   │                  │ │    └──────────────── Cluster X coord
│       │   │                  │ └───────────────────── Tile number
│       │   │                  └─────────────────────── Lane
│       │   └────────────────────────────────────────── Flow cell ID
│       └────────────────────────────────────────────── Run number
└────────────────────────────────────────────────────── Instrument ID
```

**Line 2 - Sequence:**
```
GATTTGGGGTTCAAAGCAGTATCGATCAA
```
Just your DNA sequence (A, T, C, G, and sometimes N for unknown)

**Line 4 - Quality Scores (Phred+33 encoding):**
```
!''*((((***+))%%%++)(%%%%).1
```

Each character represents a quality score:
- `!` = ASCII 33 → Phred 0 (terrible quality)
- `*` = ASCII 42 → Phred 9 (poor)
- `I` = ASCII 73 → Phred 40 (excellent)

---

## 🔢 Quality Score Decoding

### **ASCII to Phred Score:**

```
Character  ASCII  Phred  Error Rate  Accuracy
────────────────────────────────────────────
!          33     0      1 in 1      0%
"          34     1      1 in 1.3    ~20%
#          35     2      1 in 1.6    ~37%
...
*          42     9      1 in 8      87.4%
+          43     10     1 in 10     90%
0          48     15     1 in 32     96.8%
5          53     20     1 in 100    99%      ← Q20 threshold
?          63     30     1 in 1000   99.9%    ← Q30 threshold (good!)
I          73     40     1 in 10000  99.99%   ← Q40 (excellent!)
```

### **Quality Thresholds:**

| Phred Score | Accuracy | Meaning |
|-------------|----------|---------|
| **Q10** | 90% | Poor - consider trimming |
| **Q20** | 99% | Acceptable minimum |
| **Q30** | 99.9% | Good quality ✅ |
| **Q40** | 99.99% | Excellent ✅✅ |

**Industry Standard:** >80% of bases should be Q30 or higher.

---

## 📦 GZIP Compression

Your files are `.fastq.gz` = compressed with gzip.

**Why?**
- **Uncompressed**: 100 GB
- **Gzipped**: 25 GB (4x smaller!)

**How we handle it:**
```python
import gzip

# Python automatically decompresses
with gzip.open('sample.fastq.gz', 'rt') as f:
    data = f.read()
```

---

## 🎯 What Our Monitor Extracts

### **From FASTQ vs FASTA:**

| Data | FASTA | FASTQ | What We Get |
|------|-------|-------|-------------|
| **Sequence** | ✅ | ✅ | ATCG bases |
| **Quality Scores** | ❌ | ✅ | Confidence per base |
| **Read IDs** | ✅ | ✅ | Metadata |
| **Mean Quality** | ❌ | ✅ | Overall sequencing quality |
| **Q20/Q30 %** | ❌ | ✅ | Industry standard metrics |

### **What We Calculate:**

```python
# From your FASTQ.GZ file:

1. Sequence Metrics (same as FASTA):
   - GC content
   - Genome size
   - Complexity
   - ORFs
   - Homopolymers

2. Quality Metrics (NEW from FASTQ):
   - Mean Phred score
   - Q20 percentage (% bases with Q≥20)
   - Q30 percentage (% bases with Q≥30)
   - Quality distribution
   - Low-quality regions

3. Combined Quality Score:
   sequencing_quality (from FASTQ)
   +
   biological_validity (from sequence)
   =
   overall_quality
```

---

## 🔬 Real Example: What You'll See

### **Processing a FASTQ.GZ File:**

```bash
$ python examples/monitor_fastq.py sample_001.fastq.gz

================================================================================
Analyzing: sample_001.fastq.gz
================================================================================
Loading FASTQ data...
  Processed 100,000 reads...
  Loaded 100,000 reads, 15,000,000 bases

Sequencing Quality:
  Mean Quality: 36.8 (Q37)
  Q20 bases: 98.2%
  Q30 bases: 94.5%

Analyzing genomic content...

────────────────────────────────────────────────────────────────────────────────
GENOMIC ANALYSIS RESULTS
────────────────────────────────────────────────────────────────────────────────

📊 Sequence Composition:
  Genome Size: 15,000,000 bp (15.0 Mbp)
  GC Content: 36.2%
  Complexity Score: 0.87
  Max Homopolymer: 9 bases
  N-content: 0.3%

🧬 Gene Structure:
  ORF Count: 42
  Start Codon: ✅ Yes
  Stop Codon: ✅ Yes

🌱 Plant-Specific Metrics:
  Secondary Metabolite Genes: 3
  Terpene Synthases: 2
  Heterozygosity: 0.0029
  Repeat Content: 13.2%

⭐ Quality Scores:
  Sequencing Quality: 36.8 (Q37)      ← From FASTQ quality scores
  Biological Validity: 0.89            ← From sequence content
  Training Data Quality: 0.91
  Overall Quality: 0.92

────────────────────────────────────────────────────────────────────────────────

🎯 VERDICT: ✅ HIGH QUALITY - Suitable for analysis

================================================================================
```

---

## 🚀 How to Use with Your Data

### **Single File:**
```bash
python examples/monitor_fastq.py /path/to/your/sample.fastq.gz
```

### **Batch Process All Files:**
```bash
python examples/monitor_fastq.py --batch '/path/to/wgs/*.fastq.gz'
```

### **Limit Reads for Speed:**
```bash
# Process only first 50,000 reads per file (faster)
python examples/monitor_fastq.py --batch '/data/*.fastq.gz' --max-reads 50000
```

### **With Slack Alerts:**
```bash
python examples/monitor_fastq.py \
  --batch '/data/*.fastq.gz' \
  --slack-webhook 'https://hooks.slack.com/services/YOUR/WEBHOOK' \
  --output quality_report.txt
```

---

## 📊 Expected Output for Your Dataset

**Processing 100 plant WGS files:**

```
🔍 Found 100 FASTQ files to analyze

Initializing Plant Genomics Analyzer...

[1/100]
================================================================================
Analyzing: sample_001.fastq.gz
================================================================================
  Loaded 100,000 reads, 15,000,000 bases

Sequencing Quality:
  Mean Quality: 37.2
  Q20 bases: 98.5%
  Q30 bases: 95.1%

🎯 VERDICT: ✅ HIGH QUALITY - Suitable for analysis

[2/100]
================================================================================
Analyzing: sample_002.fastq.gz
================================================================================
  Loaded 100,000 reads, 12,340,000 bases

Sequencing Quality:
  Mean Quality: 28.5
  Q20 bases: 89.2%
  Q30 bases: 67.3%

⚠️  WARNINGS:
  - Low sequencing quality: 67.3% Q30 (expected >80%)
  - Mean quality below Q30: 28.5

🎯 VERDICT: ⚠️  MEDIUM QUALITY - Review recommended

...

[100/100] Processing complete

================================================================================
BATCH ANALYSIS SUMMARY
================================================================================

Total Files: 100
✅ High Quality: 87 (87.0%)
⚠️  Medium Quality: 9 (9.0%)
❌ Low Quality: 4 (4.0%)

Processing Time: 234.5 seconds (2.3s per file)

📄 Detailed report saved to: wgs_quality_report.txt

================================================================================
```

---

## 💡 Key Differences: FASTQ vs FASTA

| Feature | FASTA | FASTQ |
|---------|-------|-------|
| **Contains** | Sequence only | Sequence + Quality |
| **File size** | Smaller | Larger (quality data) |
| **Use case** | Reference genomes | Raw sequencing data |
| **Quality info** | No | Yes (per base) |
| **Your files** | ❌ | ✅ |

**Why FASTQ is better for QC:**
- Can identify low-quality bases
- Can calculate Q20/Q30 metrics
- Can detect sequencing run quality
- Industry standard for raw WGS data

---

## 🎓 Quality Interpretation

### **Good WGS Data:**
```
Mean Quality: >Q30
Q30 %: >80%
GC Content: 36-38%
Genome Size: 850-900 Mbp
Verdict: ✅ Use for analysis
```

### **Marginal WGS Data:**
```
Mean Quality: Q25-30
Q30 %: 60-80%
GC Content: 35-40%
Genome Size: 700-850 Mbp
Verdict: ⚠️  Review needed
```

### **Bad WGS Data:**
```
Mean Quality: <Q20
Q30 %: <60%
GC Content: <35% or >40%
Genome Size: <700 Mbp
Verdict: ❌ Re-sequence
```

---

**Your FASTQ.GZ files contain both the genomic sequence AND quality scores - this makes them perfect for comprehensive QC! Our monitor uses both to give you the complete picture.** ✅
