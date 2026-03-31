# TolQuant - Tolerance Test Analyzer

**Version:** 1.0.0  
**Author:** Dr. Robert Hauffe  
**Created:** March 31, 2026  
**License:** MIT License (see LICENSE file)

## Overview

TolQuant is a scientific software application designed for the analysis of glucose tolerance tests (GTT) and insulin tolerance tests (ITT). Built with PyQt6 for the user interface and powered by advanced statistical libraries, TolQuant provides researchers with a comprehensive tool for analyzing metabolic tolerance test data with scientific rigor.

## Features

### Data Analysis
- **GTT and ITT Support**: Automatically adapts analysis based on test type
- **Baseline Normalization**: ITT data is automatically normalized to baseline
- **Exclusion Handling**: Mark and exclude outlier measurements without losing raw data
- **Real-time Visualization**: Interactive plots showing mean ± SEM time courses

### Calculated Metrics

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

### Statistical Analysis
- **Two-way Repeated Measures ANOVA**: Time × Group interaction analysis
- **Post-hoc Tests**: Automatic pairwise comparisons with correction
- **Metric Comparisons**: Independent t-tests or Mann-Whitney U tests
- **Multiple Testing Correction**: Bonferroni or Tukey correction as appropriate

### Data Export
- **Excel Export**: Multi-sheet Excel files with:
  - Curve data (mean ± SEM)
  - Summary statistics
  - Sample-level details
  - Raw data with exclusion markers
  - Complete statistical test results

## Installation

### Prerequisites
- Python 3.10 or higher
- pip (Python package manager)
- Git (for cloning the repository)

### Setup from Source

1. **Clone or download the repository:**
   ```bash
   git clone <repository-url>
   cd _TolQuant
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # On Windows
   source venv/bin/activate  # On macOS/Linux
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   python main.py
   ```

## Building the Executable

### Pre-built Executable

A pre-built executable is available in the `dist` folder:
- **File:** `dist\TolQuant.exe`
- **SHA256 Checksum:** `8753913380F0BB004683B510ABA7271561C3E0232C1F8E43DD27A730677EC9DB`

Verify the checksum after download:
```powershell
(Get-FileHash -Algorithm SHA256 dist\TolQuant.exe).Hash
```

### Automated Build (Windows)

If you want to rebuild from source, run the provided build script:

```bash
build.bat
```

This script will:
- Install/upgrade PyInstaller
- Build the executable with the application icon
- Output the executable to the `dist` folder

### Manual Build

If you prefer to build manually:

1. **Install PyInstaller:**
   ```bash
   pip install pyinstaller
   ```

2. **Build the executable:**
   ```bash
   pyinstaller --onefile --windowed --icon=TolQuant_icon.ico --name=TolQuant --add-data "app;app" --clean main.py
   ```

3. **Find your executable:**
   - The compiled executable will be in the `dist` folder
   - File name: `TolQuant.exe`

### Build Options Explained

- `--onefile`: Creates a single standalone executable
- `--windowed`: Runs without a console window (GUI application)
- `--icon=TolQuant_icon.ico`: Sets the application icon
- `--name=TolQuant`: Names the output file
- `--add-data "app;app"`: Includes the app folder (use `:` separator on macOS/Linux)
- `--clean`: Removes temporary build files before building

### Distribution

To create a distributable package:

1. Copy `dist\TolQuant.exe` to a new folder
2. Include `requirements.txt`, `README.txt`, and `LICENSE`
3. Optionally include example data files
4. Compress the folder into a ZIP archive

## Usage Guide

### Starting the Application

1. **From source:** Run `python main.py` in the project directory
2. **From executable:** Double-click `TolQuant.exe`

### Inputting Data

1. **Select Test Type:** Choose GTT or ITT from the dropdown menu
2. **Set Time Points:** Enter time points as comma-separated values (e.g., `0, 15, 30, 60, 120`)
3. **Add Groups:** Click "Add Group" to create experimental groups (e.g., Control, Treatment)
4. **Enter Data:** Fill in the data table with sample measurements
   - Each row represents one sample/subject
   - Columns correspond to time points
   - Check/uncheck "Active" to include/exclude samples
   - Right-click cells to mark individual measurements as excluded

### Running Analysis

- Analysis runs automatically when you click "Run Analysis" or load example data
- Results appear in the right panel with:
  - **Plot**: Mean ± SEM time course visualization
  - **Summary Table**: Group-level statistics and comparisons
  - **Detailed Table**: Sample-level metrics
  - **ANOVA Results**: Statistical test outcomes

### Exporting Results

1. Go to `File > Export to Excel`
2. Choose a save location
3. The exported Excel file will contain multiple sheets with all results

### Loading Example Data

- Use `File > Load Example Data` to see a demonstration with realistic GTT data

## File Structure

```
_TolQuant/
├── main.py                 # Main application entry point
├── requirements.txt        # Python dependencies
├── build.bat              # Windows build script
├── README.txt             # This file
├── LICENSE                # License information
├── TolQuant_icon.ico      # Application icon
├── app/
│   ├── __init__.py
│   ├── core/
│   │   ├── analyzer.py    # Data analysis and metrics calculation
│   │   └── stats.py       # Statistical tests
│   ├── ui/
│   │   ├── input_panel.py # Data input interface
│   │   ├── plot_widget.py # Visualization component
│   │   └── results_widget.py # Results display
│   └── export/
│       └── exporter.py    # Excel export functionality
└── dist/
    └── TolQuant.exe       # Compiled executable (after build)
```

## Dependencies

The application requires the following Python packages:

- **PyQt6**: Graphical user interface
- **NumPy**: Numerical computations
- **Pandas**: Data manipulation
- **SciPy**: Scientific computing
- **Pingouin**: Statistical analysis (ANOVA, post-hoc tests)
- **Scikit-posthocs**: Post-hoc statistical tests
- **OpenPyXL**: Excel file writing
- **Matplotlib**: Plotting (embedded in PyQt)

All dependencies are listed in `requirements.txt`.

## Technical Details

### Statistical Methods

**Two-way Repeated Measures ANOVA**
- Tests for Time effect, Group effect, and Time×Group interaction
- Uses pingouin library for implementation
- Appropriate for longitudinal data with multiple groups

**Post-hoc Comparisons**
- Tukey's HSD for multiple comparisons (parametric)
- Dunn's test with Bonferroni correction (non-parametric)
- Applied when ANOVA shows significant effects

**Metric Comparisons**
- Independent samples t-test (parametric, equal variance assumed)
- Mann-Whitney U test (non-parametric alternative)
- Two-tailed tests for group differences

### Data Handling

- Excluded cells are marked but preserved in raw data
- Normalization is applied only for ITT mode
- Missing values are handled gracefully
- All calculations use active samples only

## Troubleshooting

### Application won't start
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version (3.10+ required)
- Verify no firewall is blocking PyQt6

### Statistical tests return NaN
- Ensure you have at least 2 groups with data
- Check that samples are marked as "Active"
- Verify data has sufficient variance

### Export fails
- Close any open Excel files before exporting
- Check file path doesn't contain invalid characters
- Ensure you have write permissions to the target folder

### Build fails
- Install latest PyInstaller: `pip install --upgrade pyinstaller`
- Run build script as Administrator if needed
- Check that icon file exists in project folder

## Citation

If you use TolQuant in your research, please cite:

```
Hauffe, R. (2026). TolQuant: Tolerance Test Analyzer (Version 1.0.0) [Computer software]. 
Zenodo. https://doi.org/[DOI will be assigned upon Zenodo upload]
```

## License

This software is released under the MIT License. See the LICENSE file for details.

## Disclaimer

This software is provided "as is" for research purposes. While every effort has been made to ensure accuracy, users should validate results and consult with statisticians for critical analyses. The author assumes no liability for errors or misuse.

## Support

For issues, feature requests, or questions:
- GitHub Issues: [repository issues page]
- Email: [author contact information]

## Version History

### Version 1.0.0 (March 31, 2026)
- Initial release
- GTT and ITT analysis support
- Two-way RM ANOVA with post-hoc tests
- Interactive visualization
- Excel export with multiple sheets
- Standalone executable for Windows

---

**Built for the scientific community by Dr. Robert Hauffe**
