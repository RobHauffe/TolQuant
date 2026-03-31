# TolQuant - Tolerance Test Analyzer

**Version:** 1.0.0  
**Author:** Dr. Robert Hauffe  
**Created:** March 31, 2026  
**License:** MIT License

[![DOI](https://zenodo.org/badge/DOI/[DOI-will-be-assigned].svg)](https://doi.org/[DOI-will-be-assigned])

## Overview

**TolQuant** is a scientific software application designed for the analysis of **glucose tolerance tests (GTT)** and **insulin tolerance tests (ITT)**. Built with PyQt6 for the user interface and powered by advanced statistical libraries, TolQuant provides researchers with a comprehensive tool for analyzing metabolic tolerance test data with scientific rigor.

![TolQuant Interface](docs/screenshot.png) *(Add screenshot here)*

## Features

### 📊 Data Analysis
- **GTT and ITT Support**: Automatically adapts analysis based on test type
- **Baseline Normalization**: ITT data is automatically normalized to baseline
- **Exclusion Handling**: Mark and exclude outlier measurements without losing raw data
- **Real-time Visualization**: Interactive plots showing mean ± SEM time courses

### 📈 Calculated Metrics

#### For GTT (Glucose Tolerance Test):
- **AUC**: Area under the curve (baseline-corrected)
- **Peak Above Baseline**: Maximum glucose excursion
- **Time to Peak**: Time point of maximum glucose level
- **ROC Up**: Rate of glucose rise (baseline → peak)
- **ROC Down**: Rate of glucose decline (peak → end)

#### For ITT (Insulin Tolerance Test):
- **AUC (inverted)**: Area above the curve (baseline-corrected, inverted)
- **Nadir Below Baseline**: Maximum glucose suppression
- **Time to Nadir**: Time point of minimum glucose level
- **ROC Fall**: Rate of glucose fall (baseline → nadir)
- **ROC Recovery**: Rate of counter-regulatory recovery (nadir → end)
- **Drop at t=15**: Glucose drop at 15 minutes (early clearance)
- **ROC to t=15**: Rate of change to 15 minutes

### 📉 Statistical Analysis
- **Two-way Repeated Measures ANOVA**: Time × Group interaction analysis
- **Post-hoc Tests**: Automatic pairwise comparisons with correction
- **Metric Comparisons**: Independent t-tests or Mann-Whitney U tests
- **Multiple Testing Correction**: Bonferroni or Tukey correction as appropriate

### 📤 Data Export
- **Excel Export**: Multi-sheet Excel files with:
  - Curve data (mean ± SEM)
  - Summary statistics
  - Sample-level details
  - Raw data with exclusion markers
  - Complete statistical test results

## Installation

### Quick Start (Using Executable)

1. Download the latest release from the [Releases](https://github.com/[username]/TolQuant/releases) page
2. Extract the ZIP file
3. Double-click `TolQuant.exe`
4. Start analyzing your data!

**Verify Download:**
```powershell
(Get-FileHash -Algorithm SHA256 TolQuant.exe).Hash
```
Expected: `8753913380F0BB004683B510ABA7271561C3E0232C1F8E43DD27A730677EC9DB`

### From Source (For Developers)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/[username]/TolQuant.git
   cd TolQuant
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # macOS/Linux
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   python main.py
   ```

## Usage Guide

### 1. Select Test Type
Choose **GTT** or **ITT** from the dropdown menu

### 2. Configure Time Points
Enter time points as comma-separated values (e.g., `0, 15, 30, 60, 120`)

### 3. Add Experimental Groups
Click "Add Group" to create groups (e.g., Control, Treatment)

### 4. Enter Data
- Each row = one sample/subject
- Columns = time points
- Check/uncheck "Active" to include/exclude samples
- Right-click cells to mark individual measurements as excluded

### 5. Run Analysis
Click "Run Analysis" to process data and view results

### 6. Export Results
Go to `File > Export to Excel` to save all results

## Building from Source

### Windows

```bash
# Automated build
.\build.bat

# Manual build
pip install pyinstaller
pyinstaller --onefile --windowed --icon=TolQuant_icon.ico --name=TolQuant --add-data "app;app" --clean main.py
```

The executable will be created in `dist/TolQuant.exe`

### Build Options

- `--onefile`: Single standalone executable
- `--windowed`: No console window (GUI app)
- `--icon`: Application icon
- `--add-data`: Include app folder

## Project Structure

```
TolQuant/
├── main.py                 # Main application
├── requirements.txt        # Dependencies
├── build.bat              # Build script
├── README.md              # This file
├── LICENSE                # MIT License
├── .gitignore            # Git ignore rules
├── app/
│   ├── core/
│   │   ├── analyzer.py    # Data analysis
│   │   └── stats.py       # Statistical tests
│   ├── ui/
│   │   ├── input_panel.py
│   │   ├── plot_widget.py
│   │   └── results_widget.py
│   └── export/
│       └── exporter.py    # Excel export
└── dist/
    └── TolQuant.exe       # Executable (after build)
```

## Dependencies

- **PyQt6** - Graphical user interface
- **NumPy** - Numerical computations
- **Pandas** - Data manipulation
- **SciPy** - Scientific computing
- **Pingouin** - Statistical analysis
- **Scikit-posthocs** - Post-hoc tests
- **OpenPyXL** - Excel file writing
- **Matplotlib** - Plotting

## Statistical Methods

### Two-way Repeated Measures ANOVA
Tests for Time effect, Group effect, and Time×Group interaction. Implemented using the `pingouin` library.

### Post-hoc Comparisons
- **Tukey's HSD**: Multiple comparisons (parametric)
- **Dunn's test**: Bonferroni-corrected (non-parametric)

### Metric Comparisons
- **Independent t-test**: Parametric, equal variance
- **Mann-Whitney U**: Non-parametric alternative

## Troubleshooting

### Application won't start
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Statistical tests return NaN
- Ensure at least 2 groups with data
- Check samples are marked as "Active"
- Verify data has sufficient variance

### Export fails
- Close any open Excel files
- Check file path for invalid characters
- Ensure write permissions to target folder

## Citation

If you use TolQuant in your research, please cite:

```bibtex
@software{hauffe2026tolquant,
  author = {Hauffe, Robert},
  title = {TolQuant: Tolerance Test Analyzer},
  year = {2026},
  version = {1.0.0},
  publisher = {Zenodo},
  doi = {10.5281/zenodo.[DOI-will-be-assigned]},
  url = {https://github.com/[username]/TolQuant}
}
```

## License

This software is released under the [MIT License](LICENSE).

## Disclaimer

This software is provided "as is" for research purposes. While every effort has been made to ensure accuracy, users should validate results and consult with statisticians for critical analyses. The author assumes no liability for errors or misuse.

## Support

- **Issues:** [GitHub Issues](https://github.com/[username]/TolQuant/issues)
- **Email:** [Author contact information]
- **Documentation:** See `README.txt` for detailed guide

## Version History

### v1.0.0 (March 31, 2026)
- ✨ Initial release
- 📊 GTT and ITT analysis support
- 📈 Two-way RM ANOVA with post-hoc tests
- 📉 Interactive visualization
- 📤 Excel export with multiple sheets
- 💻 Standalone Windows executable

---

**Built for the scientific community by Dr. Robert Hauffe**

[![GitHub stars](https://img.shields.io/github/stars/[username]/TolQuant?style=social)](https://github.com/[username]/TolQuant/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/[username]/TolQuant?style=social)](https://github.com/[username]/TolQuant/network)
[![GitHub issues](https://img.shields.io/github/issues/[username]/TolQuant)](https://github.com/[username]/TolQuant/issues)
