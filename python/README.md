# Warcry Data Python Tools

## Overview

**What it does:** Data processing pipeline for Warcry tabletop game data  
**Key Features:** Schema validation, multi-format export

### What You Can Accomplish
- ✅ **Validate Game Data** - Ensure all fighters, abilities and factions meet quality standards
- ✅ **Export Multiple Formats** - Generate JSON, HTML, CSV and Tabletop Simulator files
- ✅ **Process 1300+ Fighters** - Handle the complete Warcry dataset efficiently  
- ✅ **Develop New Features** - Extend the pipeline with new export formats or validation rules

## Quick Start (Beginners)

### Prerequisites Check
Before starting, verify you have:
- **Operating System**: Windows, macOS or Linux
- **Terminal Access**: Command Prompt (Windows), Terminal (Mac/Linux) or PowerShell
- **Internet Connection**: For downloading Python and dependencies

### Step-by-Step Setup

#### 1. Install Python
- Download [Python 3.8+](https://www.python.org/downloads/) for your operating system
- **Important**: Check "Add Python to PATH" during installation
- **Important**: Check "Install pip" during installation

#### 2. Verify Installation
Open your terminal and test:
```bash
python --version
# Should show: Python 3.8.0 or higher

pip --version  
# Should show: pip 20.0.0 or higher
```

#### 3. Navigate to Project
```bash
# Navigate to the warcry_data/python directory
cd path/to/warcry_data/python

# Verify you're in the right place
ls
# Should show: requirements.txt, validation.py, export_data.py
```

#### 4. Install Dependencies
```bash
python -m pip install -r requirements.txt
```
**Expected output**: Multiple packages installing successfully

#### 5. Verify Setup
```bash
python validation.py
```

**✅ Success looks like:**
```
INFO - Starting data processing pipeline
INFO - Loaded 1312 fighters across all Grand Alliances
INFO - Loaded 972 abilities across all warbands
INFO - Data validation passed
```

**❌ If you see errors:**
- Check Python version: `python --version`
- Reinstall dependencies: `pip install -r requirements.txt --force-reinstall`
- See [Troubleshooting](#troubleshooting) section below

### Your First Data Export
```bash
# Export all formats to local folder (safe for testing)
python export_data.py -local

# Check your results
ls local/
# Should show: fighters.json, abilities.json, fighters.html, etc.
```

## Common Workflows

### Validate Game Data
```bash
# Validate all data against JSON schemas
python validation.py

# Validate specific data folder
python validation.py --data /path/to/custom/data
```

### Export Multiple Formats
```bash
# Export to local folder (for testing)
python export_data.py -local

# Export to docs/ folder (for GitHub Pages)
python export_data.py
```

### Development & Testing
```bash
# Make your changes to data files
# Always validate before committing
python validation.py

# Test your changes locally
python export_data.py -local

# Verify outputs look correct
open local/fighters.html  # View in browser
```

## Architecture Overview

### Pipeline Components
Our architecture includes:

- **`warband_pipeline.py`** - Main orchestrator coordinating all operations
- **`data_loading.py`** - Efficient file loading across all Grand Alliances  
- **`data_processing.py`** - Optimized ID/ability/faction assignment
- **Export Modules**:
  - `json_exporter.py` - JSON formats for APIs
  - `tts_exporter.py` - Tabletop Simulator integration
  - `html_exporter.py` - Human-readable tables and CSV
- **Quality Systems**:
  - `validation_system.py` - Structured validation with detailed error reporting
  - `business_rules.py` - Configurable validation and export rules
  - `logging_config.py` - Enterprise logging with performance monitoring

### Modular Design Benefits
- **Single Responsibility** - Each component has one focused purpose
- **Extensible** - Add new export formats without touching existing code
- **Testable** - Components can be tested independently
- **Maintainable** - Clear separation of concerns
- **Type Safe** - Modern type annotations throughout

### Performance Features
- **Optimized Algorithms** - O(n+m) complexity for ability assignment
- **Efficient File Loading** - UTF-8 with graceful legacy support
- **Batch Processing** - Handle 1300+ fighters efficiently
- **Memory Optimized** - Process large datasets without excessive memory use

## Development Guide

### Environment Setup
For contributing to the project:

```bash
# Create virtual environment (recommended)
python -m venv warcry-env

# Activate it
# Windows:
warcry-env\Scripts\activate
# Mac/Linux:
source warcry-env/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### IDE Recommendations
- **PyCharm Community Edition** - Full-featured IDE with debugging
- **VS Code** - Lightweight with Python extension

### Contributing Workflow
1. **Make Changes** - Edit data files or Python code
2. **Validate** - `python validation.py` 
3. **Test Locally** - `python export_data.py -local`
4. **Verify Output** - Check generated files look correct
5. **Submit PR** - All validation must pass

### Testing & Quality Assurance
```bash
# Comprehensive validation
python validation.py

# Export verification  
python export_data.py -local
diff docs/ local/  # Compare outputs

# Performance testing
python -c "
from data_parsing.logging_config import PerformanceTimer
from data_parsing.warband_pipeline import WarbandDataPipeline
with PerformanceTimer('Full Pipeline'):
    pipeline = WarbandDataPipeline()
"
```

## Scripts Reference

### `validation.py`
**Purpose**: Validate all game data against JSON schemas and business rules  
**Usage**: `python validation.py [--data path]`  
**Use Cases**: CI/CD pipeline, pre-commit validation, data quality assurance

### `export_data.py`  
**Purpose**: Generate all output formats from source data  
**Usage**: `python export_data.py [-local]`  
**Outputs**: JSON, HTML, CSV, TTS format, localized data

## Troubleshooting

### Common Issues

**"python: command not found"**
- Python not installed or not in PATH
- Try `python3` instead of `python`
- Reinstall Python with "Add to PATH" checked

**"No module named 'jsonschema'"**
- Dependencies not installed
- Run: `pip install -r requirements.txt`

**"Permission denied" errors**
- Try: `python -m pip install --user -r requirements.txt`
- Or run terminal as administrator

**Validation fails with schema errors**
- Check data file format matches examples
- Ensure all required fields are present
- Verify JSON syntax is valid

**"FileNotFoundError" during export**
- Ensure you're in the `warcry_data/python` directory
- Check that `data/` folder exists and contains warband files

### Getting Help
- **Check the logs** - Error messages usually indicate the specific issue
- **Verify file paths** - Ensure you're in the correct directory
- **Test with minimal data** - Start with a single warband to isolate issues
- **Check GitHub Issues** - Common problems may already have solutions

## Next Steps

After successful setup:
1. **Explore the data** - Look at `data/chaos/beasts_of_chaos/` to understand structure
2. **Try modifications** - Edit a fighter's stats and re-export
3. **Understand validation** - Intentionally break something to see error reporting
4. **Extend functionality** - Add new export formats or validation rules

**Ready to contribute?** See the main repository README for contribution guidelines.
