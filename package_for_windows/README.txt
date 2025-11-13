# Cannabis WGS Quality Analyzer for Windows

**Ready-to-use package for analyzing your FASTQ files at F:\wgs\PRJNA734114**

## 📦 What's in This Package

1. **monitor_fastq_windows.py** - Main analysis script
2. **WINDOWS_INSTRUCTIONS.md** - Step-by-step guide
3. **PRJNA734114_INFO.txt** - About your Cannabis data
4. **FASTQ_FORMAT_GUIDE.md** - Understanding FASTQ files
5. **QUICKSTART_FASTQ.md** - Quick reference
6. **run_analysis.bat** - Double-click to run (Windows)

## 🚀 Quick Start (3 Steps)

### Step 1: Extract This Package
Extract all files to your Desktop: `C:\Users\YourName\Desktop\cannabis_wgs_analyzer\`

### Step 2: Edit run_analysis.bat
Open `run_analysis.bat` in Notepad and change `YourName` to your actual Windows username.

### Step 3: Double-Click run_analysis.bat
That's it! The analysis will start automatically.

## 📊 What You'll Get

```
🔍 Found 347 FASTQ files

[1/347] SRR14947855.fastq.gz → ✅ HIGH QUALITY
[2/347] SRR14947856.fastq.gz → ✅ HIGH QUALITY
...

Total: 347 files
✅ High Quality: 298 (86%)
⚠️  Medium: 34 (10%)
❌ Low: 15 (4%)

📄 Report: cannabis_quality_report.txt
```

## 🔧 Requirements

- Windows 10 or 11
- Python 3.7+ installed ([Download](https://www.python.org/downloads/))
- Your FASTQ files at `F:\wgs\PRJNA734114\`

## 📚 Documentation

- **WINDOWS_INSTRUCTIONS.md** - Full usage guide
- **FASTQ_FORMAT_GUIDE.md** - Understanding your data
- **PRJNA734114_INFO.txt** - About Cannabis sativa WGS

## 💡 Manual Usage

If you prefer command line:

```cmd
cd C:\Users\YourName\Desktop\cannabis_wgs_analyzer
python monitor_fastq_windows.py --batch "F:\wgs\PRJNA734114\*.fastq.gz"
```

## ❓ Troubleshooting

**Python not found?**
- Install from https://www.python.org/downloads/
- Make sure to check "Add Python to PATH"

**Files not found?**
- Check your data is at `F:\wgs\PRJNA734114\`
- Run: `dir F:\wgs\PRJNA734114` to verify

**Too slow?**
- Edit run_analysis.bat and add `--max-reads 50000`

## 📞 Support

See WINDOWS_INSTRUCTIONS.md for detailed help.

---

**Ready to analyze your Cannabis WGS data!** 🌱
