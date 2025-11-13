# Running on Windows - Instructions for F:\wgs\PRJNA734114

## 🎯 **Quick Start (3 Steps)**

### **Step 1: Download the Script**

Copy this file to your Windows machine:
```
/home/user/oss_srv/diffusion_monitor/examples/monitor_fastq_windows.py
```

Save it to: `C:\Users\YourName\Desktop\monitor_fastq_windows.py`

### **Step 2: Open Command Prompt**

Press `Win + R`, type `cmd`, press Enter

### **Step 3: Run the Script**

#### **Analyze a single file:**
```cmd
cd C:\Users\YourName\Desktop
python monitor_fastq_windows.py "F:\wgs\PRJNA734114\sample_001.fastq.gz"
```

#### **Analyze all files:**
```cmd
python monitor_fastq_windows.py --batch "F:\wgs\PRJNA734114\*.fastq.gz"
```

---

## 📊 **What You'll See**

```
🔍 Found 347 FASTQ files to analyze

[1/347]
================================================================================
Analyzing: SRR14947855.fastq.gz
================================================================================
Loading FASTQ data...
  Loaded 100,000 reads, 15,000,000 bases

Sequencing Quality:
  Mean Quality: Q36
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

⭐ Quality Scores:
  Sequencing Quality: Q36
  Q30 Percentage: 94.5%

────────────────────────────────────────────────────────────────────────────────

🎯 VERDICT: ✅ HIGH QUALITY - Suitable for analysis

================================================================================

[2/347] ...

================================================================================
BATCH ANALYSIS SUMMARY
================================================================================

Total Files: 347
✅ High Quality: 298 (86.0%)
⚠️  Medium Quality: 34 (9.8%)
❌ Low Quality: 15 (4.3%)

📄 Detailed report saved to: wgs_quality_report.txt
```

---

## 📁 **What is PRJNA734114?**

**NCBI BioProject**: [PRJNA734114](https://www.ncbi.nlm.nih.gov/bioproject/PRJNA734114)

This is **Cannabis sativa** WGS data! The monitoring script will analyze:
- Sequencing quality (Q20/Q30 scores)
- GC content (~38% expected for cannabis)
- Sequence complexity
- Genome completeness

---

## 🔧 **Requirements**

**Python 3.7+** (check with `python --version`)

If you don't have Python:
1. Download from [python.org](https://www.python.org/downloads/)
2. Install with "Add to PATH" checked
3. Restart Command Prompt

**No other dependencies needed!** This standalone script only uses Python standard library.

---

## 💡 **Advanced Usage**

### **Process specific samples:**
```cmd
python monitor_fastq_windows.py --batch "F:\wgs\PRJNA734114\SRR1494*.fastq.gz"
```

### **Limit reads for faster processing:**
```cmd
python monitor_fastq_windows.py --batch "F:\wgs\PRJNA734114\*.fastq.gz" --max-reads 50000
```

### **Custom output file:**
```cmd
python monitor_fastq_windows.py --batch "F:\wgs\PRJNA734114\*.fastq.gz" --output cannabis_qc_report.txt
```

---

## 📄 **Output Report Format**

The script creates a text file (`wgs_quality_report.txt`) with:

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

File: SRR14947855.fastq.gz
Verdict: ✅ HIGH QUALITY - Suitable for analysis
  Q30: 94.5%
  GC: 36.20%

File: SRR14947856.fastq.gz
Verdict: ⚠️  MEDIUM QUALITY - Review recommended
  Q30: 76.3%
  GC: 34.80%

File: SRR14947857.fastq.gz
Verdict: ❌ LOW QUALITY - Do not use
  Q30: 58.2%
  GC: 28.50%

...
```

---

## 🎯 **Understanding Results**

### **HIGH QUALITY (✅)**
- Q30 >80%
- GC 35-40%
- Good complexity
- **→ Use for ML training**

### **MEDIUM QUALITY (⚠️)**
- Q30 60-80%
- Some issues
- **→ Review manually**

### **LOW QUALITY (❌)**
- Q30 <60%
- Major issues
- **→ Discard or re-sequence**

---

## 🚀 **Next Steps After Analysis**

1. **Review the report:**
   ```cmd
   notepad wgs_quality_report.txt
   ```

2. **Filter high-quality files:**
   - Look for "HIGH QUALITY" verdicts
   - Use those files for your ML pipeline

3. **Investigate issues:**
   - Check warnings for low-quality samples
   - Decide if re-sequencing is needed

---

## ❓ **Troubleshooting**

### **Error: "python: command not found"**
- Python not installed or not in PATH
- Solution: Install Python from python.org

### **Error: "No such file or directory"**
- Check file path uses backslashes: `F:\wgs\...`
- Use quotes around paths with spaces

### **Error: "Permission denied"**
- Run Command Prompt as Administrator
- Or copy files to `C:\Users\YourName\Documents\`

### **Script runs too slow**
- Use `--max-reads 50000` to analyze fewer reads
- Still gives accurate quality assessment

---

## 🎓 **About PRJNA734114**

This appears to be **Cannabis sativa** (hemp/marijuana) whole genome sequencing data.

**Expected characteristics:**
- Genome size: ~850-900 Mbp
- GC content: ~36-38%
- Heterozygous: ~3 SNPs per kb
- Contains cannabinoid biosynthesis genes (THCA, CBDA synthases)
- Contains terpene synthase genes

Your analysis will tell you:
- Which samples have good sequencing quality
- Which samples are complete genomes
- Which are suitable for downstream analysis
- Which should be excluded from ML training

---

## 📞 **Support**

If you encounter issues:
1. Check Python version: `python --version` (need 3.7+)
2. Check file exists: `dir "F:\wgs\PRJNA734114"`
3. Try with one file first before batch processing
4. Check the error message carefully

---

**Ready to analyze your cannabis WGS data!** 🌱

Start with:
```cmd
python monitor_fastq_windows.py "F:\wgs\PRJNA734114\*.fastq.gz" --batch
```
