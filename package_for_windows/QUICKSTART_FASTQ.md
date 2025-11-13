# Quick Start: Monitor Your FASTQ.GZ Files

**For: Plant WGS Data in FASTQ.GZ Format**

---

## 🚀 Get Started in 3 Steps (5 Minutes)

### **Step 1: Install Dependencies**

```bash
cd /home/user/oss_srv/diffusion_monitor
pip install scipy numpy requests
```

### **Step 2: Test with Sample Data**

```bash
# Test the parser works
python examples/monitor_fastq.py --help
```

### **Step 3: Analyze Your First File**

```bash
python examples/monitor_fastq.py /path/to/your/sample.fastq.gz
```

**That's it!** You'll see:
- Sequencing quality (Q scores)
- Genomic content analysis
- Plant-specific metrics
- Pass/Fail verdict

---

## 📊 Example Output

```bash
$ python examples/monitor_fastq.py sample_001.fastq.gz

================================================================================
Analyzing: sample_001.fastq.gz
================================================================================
Loading FASTQ data...
  Loaded 100,000 reads, 15,000,000 bases

Sequencing Quality:
  Mean Quality: 36.8
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
  Sequencing Quality: 36.8 (Q37)
  Biological Validity: 0.89
  Training Data Quality: 0.91
  Overall Quality: 0.92

────────────────────────────────────────────────────────────────────────────────

🎯 VERDICT: ✅ HIGH QUALITY - Suitable for analysis

================================================================================
```

---

## 📦 Batch Process All Your Files

### **Process Hundreds of Files:**

```bash
python examples/monitor_fastq.py \
  --batch '/path/to/your/wgs_data/*.fastq.gz' \
  --max-reads 100000 \
  --output quality_report.txt
```

**Output:**
```
🔍 Found 347 FASTQ files to analyze

[1/347] Analyzing: sample_001.fastq.gz
  Loaded 100,000 reads, 15,000,000 bases
  🎯 VERDICT: ✅ HIGH QUALITY

[2/347] Analyzing: sample_002.fastq.gz
  Loaded 100,000 reads, 12,340,000 bases
  🎯 VERDICT: ⚠️  MEDIUM QUALITY

...

================================================================================
BATCH ANALYSIS SUMMARY
================================================================================

Total Files: 347
✅ High Quality: 298 (86.0%)
⚠️  Medium Quality: 34 (9.8%)
❌ Low Quality: 15 (4.3%)

Processing Time: 812.5 seconds (2.3s per file)

📄 Detailed report saved to: quality_report.txt
```

---

## 🎯 Understanding the Results

### **Quality Verdict:**

| Verdict | Criteria | Action |
|---------|----------|--------|
| ✅ **HIGH** | Q30>80%, GC~36%, Quality>0.7 | Use for analysis |
| ⚠️  **MEDIUM** | Q30=60-80%, some issues | Review manually |
| ❌ **LOW** | Q30<60%, major issues | Discard/re-sequence |

### **Key Metrics:**

**Sequencing Quality:**
- **Q30%**: % of bases with quality score ≥30 (99.9% accuracy)
- **Target**: >80% Q30
- **Your data**: Should be 85-95% for good Illumina runs

**Genomic Quality:**
- **GC Content**: Should be ~36-38% for your plant
- **Genome Size**: Should be ~850-900 Mbp
- **ORF Count**: Expect many (15-30 per 100kb)

**Plant Metrics:**
- **Secondary Metabolite Genes**: Expected 3-5
- **Terpene Synthases**: Expected 8-10
- **Heterozygosity**: ~0.003 (3 SNPs/kb) typical

---

## ⚡ Speed Options

### **Fast Mode** (analyze first 50K reads):
```bash
python examples/monitor_fastq.py sample.fastq.gz --max-reads 50000
```

### **Full Analysis** (all reads):
```bash
python examples/monitor_fastq.py sample.fastq.gz --max-reads 0
```

**Recommendation**: Use `--max-reads 100000` for good balance (fast + accurate)

---

## 📧 Get Alerts

### **Add Slack Notifications:**

```bash
python examples/monitor_fastq.py \
  --batch '/data/*.fastq.gz' \
  --slack-webhook 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
```

When a low-quality sample is found, you'll get a Slack message:

```
🚨 Low Quality WGS Sample
Sample: sample_099.fastq.gz failed quality checks

Primary Reason: Low sequencing quality: 67.3% Q30 (expected >80%)

Metrics:
  Training Quality: 0.52
  Sequencing Quality: 28.5
  Q30 %: 67.3%
```

---

## 🔍 What to Look For

### **Good Sample:**
```
✅ Q30 %: >80%
✅ GC Content: 36-38%
✅ Genome Size: 850-900 Mbp
✅ ORF Count: >20
✅ No warnings
```

### **Bad Sample (Common Issues):**

**Issue 1: Low Sequencing Quality**
```
❌ Q30 %: 65%  (should be >80%)
⚠️  Mean Quality: Q26 (should be >Q30)
Action: Re-sequence or discard
```

**Issue 2: Wrong GC Content**
```
❌ GC Content: 28%  (should be ~36%)
⚠️  GC deviation: 8%
Possible causes: Contamination, wrong species
Action: Check for bacterial/fungal contamination
```

**Issue 3: Incomplete Data**
```
❌ Genome Size: 420 Mbp  (should be ~850)
⚠️  ORF Count: 5 (too few)
Possible causes: Incomplete assembly, low coverage
Action: Re-sequence with higher coverage
```

**Issue 4: Low Complexity**
```
❌ Complexity: 0.32  (should be >0.7)
⚠️  Homopolymer: 156 bases (huge!)
Possible causes: Sequencing artifact, adapter contamination
Action: Re-process or trim adapters
```

---

## 📂 Output Files

### **Individual Analysis:**
- Prints to console
- No file created (unless you redirect output)

### **Batch Analysis:**
- **Console**: Summary statistics
- **File** (`quality_report.txt`): Detailed per-sample results

**Report Format:**
```
================================================================================
PLANT WGS QUALITY REPORT
================================================================================

Total Samples: 347
High Quality: 298 (86.0%)
Medium Quality: 34 (9.8%)
Low Quality: 15 (4.3%)

================================================================================
DETAILED RESULTS
================================================================================

File: sample_001.fastq.gz
Verdict: GREEN
  Genome Size: 863.2 Mbp
  GC Content: 36.4%
  Sequencing Quality: Q37
  Q30 %: 94.5%
  Training Quality: 0.91

File: sample_002.fastq.gz
Verdict: YELLOW
  Genome Size: 812.1 Mbp
  GC Content: 34.8%
  Sequencing Quality: Q29
  Q30 %: 76.3%
  Training Quality: 0.68
  Warnings:
    - Low sequencing quality: 76.3% Q30 (expected >80%)
    - Genome size slightly small

...
```

---

## 🎓 Common Questions

**Q: How long does it take?**
A: ~2-3 seconds per file (with `--max-reads 100000`)

**Q: Do I need to decompress .gz files first?**
A: No! The script handles .gz files automatically

**Q: Can I analyze uncompressed .fastq files?**
A: Yes! Works with both .fastq and .fastq.gz

**Q: How many reads should I analyze?**
A: 100,000 reads gives good accuracy. More is better but slower.

**Q: What if I have paired-end reads (R1/R2)?**
A: Analyze each file separately, or concatenate them first

**Q: Can I use this for other plants?**
A: Yes! Just adjust the expected values in the script

---

## 🔧 Customize for Your Plant

Edit `examples/monitor_fastq.py` and change these lines:

```python
# Around line 264:
analyzer.EXPECTED_GENOME_SIZE = 850_000_000  # Your plant's genome size (bp)
analyzer.EXPECTED_GC_CONTENT = 0.36          # Your plant's GC%
analyzer.EXPECTED_HETEROZYGOSITY = 0.003     # Your plant's SNP density
```

---

## 📚 More Information

- **Full Guide**: See `PLANT_WGS_INTEGRATION_GUIDE.md`
- **FASTQ Format**: See `FASTQ_FORMAT_GUIDE.md`
- **What We Measure**: See `WHAT_ARE_WE_VISUALIZING.md`
- **Architecture**: See `USE_CASE_1_README.md`

---

## 🎯 Next Steps

1. ✅ **Test with one file** (5 min)
2. ✅ **Process a small batch** (30 min)
3. ✅ **Set up Slack alerts** (10 min)
4. ✅ **Process all your data** (few hours)
5. ✅ **Use high-quality files for ML** (your analysis)

---

**Ready to analyze your FASTQ.GZ files? Just run:**

```bash
python examples/monitor_fastq.py /path/to/your/first_file.fastq.gz
```

🚀 **It's that simple!**
