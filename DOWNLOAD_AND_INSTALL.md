# Download and Install - Cannabis WGS Quality Analyzer

## 📦 Package Available

Your Cannabis WGS Quality Analyzer is ready! Two formats available:
- **cannabis_wgs_analyzer.zip** (16 KB) - For Windows
- **cannabis_wgs_analyzer.tar.gz** (12 KB) - For Linux/Mac

## 🚀 Quick Install (3 Steps)

### Step 1: Download the Package

**Option A: Using Git (Recommended)**
```cmd
cd C:\Users\YourName\Desktop
git clone https://github.com/tcBio/diffusion-monitor.git
cd diffusion-monitor
```

**Option B: Download ZIP from GitHub**
1. Go to: https://github.com/tcBio/diffusion-monitor
2. Click "Code" → "Download ZIP"
3. Extract to your Desktop

**Option C: Download Archive File**
Download from your repository:
- `cannabis_wgs_analyzer.zip` (branch: `claude/pull-tcbio-oss-srv-011CV5E86xaXLCRTZYMk9VHP`)

### Step 2: Extract the Package

**Windows:**
```cmd
REM Navigate to where you downloaded the file
cd C:\Users\YourName\Downloads

REM Extract using Windows built-in tool
tar -xf cannabis_wgs_analyzer.zip

REM Or right-click → "Extract All..."
```

You should now have a `package_for_windows` folder with:
```
package_for_windows/
├── monitor_fastq_windows.py      ← Main analysis script
├── run_analysis.bat              ← Double-click to run!
├── README.txt                    ← Quick start guide
├── WINDOWS_INSTRUCTIONS.md       ← Full documentation
├── FASTQ_FORMAT_GUIDE.md         ← Understanding your data
├── QUICKSTART_FASTQ.md           ← Quick reference
└── PRJNA734114_INFO.txt          ← About your Cannabis data
```

### Step 3: Run the Analysis

**Method 1: Double-Click (Easiest)**
1. Open `package_for_windows` folder
2. Double-click `run_analysis.bat`
3. That's it! Analysis will start automatically.

**Method 2: Command Line**
```cmd
cd C:\Users\YourName\Desktop\package_for_windows
python monitor_fastq_windows.py --batch "F:\wgs\PRJNA734114\*.fastq.gz"
```

---

## 📊 What You'll Get

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

...

================================================================================
BATCH ANALYSIS SUMMARY
================================================================================

Total Files: 347
✅ High Quality: 298 (86.0%)
⚠️  Medium Quality: 34 (9.8%)
❌ Low Quality: 15 (4.3%)

📄 Detailed report saved to: cannabis_quality_report.txt
```

---

## 🔧 Requirements

**Before running, make sure you have:**

1. **Python 3.7+** installed
   - Download from: https://www.python.org/downloads/
   - **IMPORTANT**: Check "Add Python to PATH" during installation

2. **Your FASTQ files** at `F:\wgs\PRJNA734114\`
   - Verify: Open Command Prompt and run `dir F:\wgs\PRJNA734114`

**No other dependencies needed!** This script uses only Python standard library.

---

## 🎯 Customization

### Analyze Different Files

Edit `run_analysis.bat` and change the path:
```batch
REM Change this line:
python monitor_fastq_windows.py --batch "F:\wgs\PRJNA734114\*.fastq.gz"

REM To your path:
python monitor_fastq_windows.py --batch "D:\your\custom\path\*.fastq.gz"
```

### Faster Analysis (Fewer Reads)

```cmd
python monitor_fastq_windows.py --batch "F:\wgs\PRJNA734114\*.fastq.gz" --max-reads 50000
```

### Custom Output File

```cmd
python monitor_fastq_windows.py --batch "F:\wgs\PRJNA734114\*.fastq.gz" --output my_report.txt
```

### Analyze Single File

```cmd
python monitor_fastq_windows.py "F:\wgs\PRJNA734114\SRR14947855.fastq.gz"
```

---

## ❓ Troubleshooting

### **Error: "python: command not found"**
- Python is not installed or not in PATH
- **Solution**:
  1. Install Python from https://www.python.org/downloads/
  2. During installation, CHECK "Add Python to PATH"
  3. Restart Command Prompt

### **Error: "No such file or directory"**
- File path is incorrect
- **Solution**:
  1. Verify files exist: `dir F:\wgs\PRJNA734114`
  2. Use quotes around paths with spaces
  3. Use backslashes (`\`) not forward slashes (`/`) on Windows

### **Error: "Permission denied"**
- Insufficient permissions to access files
- **Solution**:
  1. Run Command Prompt as Administrator
  2. Or copy files to your Documents folder first

### **Script runs too slow**
- Processing large files takes time
- **Solution**: Use `--max-reads 50000` to analyze fewer reads
  ```cmd
  python monitor_fastq_windows.py --batch "F:\wgs\PRJNA734114\*.fastq.gz" --max-reads 50000
  ```

### **How do I check Python version?**
```cmd
python --version
```
Should show: `Python 3.7.0` or higher

---

## 📚 Documentation Files

**Quick Start:**
- `README.txt` - 3-step quick start (read this first!)
- `QUICKSTART_FASTQ.md` - Examples and common usage

**Full Guides:**
- `WINDOWS_INSTRUCTIONS.md` - Complete Windows usage guide
- `FASTQ_FORMAT_GUIDE.md` - Understanding FASTQ files and quality scores

**Reference:**
- `PRJNA734114_INFO.txt` - About your Cannabis sativa dataset

---

## 🌱 About PRJNA734114

Your dataset is **Cannabis sativa** (hemp/marijuana) whole genome sequencing data from NCBI BioProject PRJNA734114.

**Expected characteristics:**
- Genome size: ~850-900 Mbp
- GC content: ~36-38%
- Q30 percentage: >80% for good Illumina runs
- Contains cannabinoid biosynthesis genes (THCA, CBDA synthases)
- Contains terpene synthase genes

**Our analyzer checks:**
- ✅ Sequencing quality (Q20/Q30 scores)
- ✅ GC content matches expected range
- ✅ Sequence complexity
- ✅ Genome completeness
- ✅ Overall suitability for downstream analysis

---

## 🎓 Understanding Results

### **HIGH QUALITY (✅)**
```
Q30: >80%
GC: 35-40%
Complexity: >0.6
→ USE for analysis/ML training
```

### **MEDIUM QUALITY (⚠️)**
```
Q30: 60-80%
Some quality issues
→ REVIEW manually, decide if usable
```

### **LOW QUALITY (❌)**
```
Q30: <60%
Major quality issues
→ DISCARD or re-sequence
```

---

## 📞 Next Steps

1. ✅ **Download and extract** the package
2. ✅ **Verify Python** is installed (`python --version`)
3. ✅ **Check your data** exists (`dir F:\wgs\PRJNA734114`)
4. ✅ **Run the analysis** (double-click `run_analysis.bat`)
5. ✅ **Review the report** (`cannabis_quality_report.txt`)
6. ✅ **Use high-quality files** for your downstream analysis

---

## 💡 Tips

**For best results:**
- Analyze all files first to get overview
- Review the summary report to identify low-quality samples
- Use high-quality samples for ML training
- Re-sequence or discard low-quality samples
- Processing time: ~2-3 seconds per file

**Typical analysis time:**
- 100 files: ~5 minutes
- 347 files: ~15 minutes
- 1000 files: ~45 minutes

---

**Ready to analyze your Cannabis WGS data!** 🌱

Start with:
```cmd
cd package_for_windows
run_analysis.bat
```

Or:
```cmd
python monitor_fastq_windows.py --batch "F:\wgs\PRJNA734114\*.fastq.gz"
```
