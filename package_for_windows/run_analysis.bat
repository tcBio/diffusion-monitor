@echo off
REM Cannabis WGS Quality Analyzer - Quick Run Script
REM This script analyzes all FASTQ files in F:\wgs\PRJNA734114

echo ================================================================================
echo Cannabis WGS Quality Analyzer
echo ================================================================================
echo.
echo Analyzing FASTQ files at F:\wgs\PRJNA734114
echo.
echo This will:
echo   - Process all .fastq.gz files in the directory
echo   - Analyze 100,000 reads per file (fast mode)
echo   - Generate a quality report
echo.
echo Press Ctrl+C to cancel, or
pause

REM Change to the directory where this script is located
cd /d "%~dp0"

echo.
echo Starting analysis...
echo.

python monitor_fastq_windows.py --batch "F:\wgs\PRJNA734114\*.fastq.gz" --output cannabis_quality_report.txt

echo.
echo ================================================================================
echo Analysis Complete!
echo ================================================================================
echo.
echo Report saved to: cannabis_quality_report.txt
echo.
echo You can open the report with:
echo   notepad cannabis_quality_report.txt
echo.
pause
