# Packaging Directory

This directory contains PyInstaller specifications and packaging configurations for building SCADA-IDS-KC executables.

## Files Overview

### `SCADA-IDS-KC-main.spec`
**Purpose:** Main PyInstaller specification file
- Defines how to package the application into a single executable
- Handles data files, hidden imports, and dependencies
- Supports both with-Npcap and standalone builds
- Automatically detects and includes Npcap installer if available

**Key Features:**
- **Automatic Npcap Detection:** Includes Npcap installer if present in `../npcap/`
- **Data File Inclusion:** Bundles configuration files, models, and documentation
- **Hidden Imports:** Ensures all required modules are included
- **Cross-Platform Support:** Works on Windows with proper dependencies

### Build Outputs

#### `dist/` Directory
Contains the final built executable:
- `SCADA-IDS-KC.exe` - Main application executable
- Supporting DLLs and libraries (if any)

#### `build/` Directory
Contains PyInstaller build artifacts:
- Temporary files and analysis results
- Build logs and dependency information
- Can be safely deleted after successful build

## PyInstaller Configuration Details

### Data Files Included
```python
datas = [
    ('../config', 'config'),           # Configuration files
    ('../src', 'src'),                 # Source code
    ('../models', 'models'),           # ML models
    ('../npcap/npcap-installer.exe', 'npcap'),  # Npcap installer (if available)
    ('../npcap/fallback_info.json', 'npcap')   # Npcap fallback info (if available)
]
```

### Hidden Imports
```python
hiddenimports = [
    'scada_ids',                       # Main package
    'scada_ids.settings',              # Settings module
    'scada_ids.controller',            # Main controller
    'scada_ids.capture',               # Packet capture
    'scada_ids.features',              # Feature extraction
    'scada_ids.ml',                    # Machine learning
    'scada_ids.notifier',              # Notifications
    'scada_ids.packet_logger',         # Logging
    'scada_ids.sikc_config',           # Configuration
    'scada_ids.npcap_manager',         # Npcap management
    'ui',                              # GUI package
    'ui.main_window',                  # Main window
    'numpy._core',                     # NumPy core modules
    'numpy._core._multiarray_umath',   # NumPy internals
    'numpy._core._multiarray_tests'    # NumPy tests
]
```

## Build Process Integration

### Npcap Detection Logic
The spec file automatically detects Npcap installer:
```python
# Add Npcap installer if available
import os
npcap_installer = '../npcap/npcap-installer.exe'
npcap_fallback_info = '../npcap/fallback_info.json'

if os.path.exists(npcap_installer):
    datas.append((npcap_installer, 'npcap'))
    print(f"Including Npcap installer: {npcap_installer}")
else:
    print("WARNING: Npcap installer not found - packet capture may require manual Npcap installation")
```

### Build Variants
The same spec file supports both build variants:

#### With Npcap Build
- Npcap installer present in `../npcap/`
- Automatically included in executable
- Results in larger file size (~50-80 MB)
- Enables auto-installation capabilities

#### Standalone Build
- Npcap installer absent or moved
- Smaller executable size (~30-50 MB)
- Requires system-installed Npcap
- Fallback detection still works

## Manual Build Commands

### Basic Build
```bash
cd packaging
pyinstaller --clean SCADA-IDS-KC-main.spec
```

### Clean Build (Recommended)
```bash
cd packaging
pyinstaller --clean SCADA-IDS-KC-main.spec
```

### Debug Build
```bash
cd packaging
pyinstaller --clean --debug=all SCADA-IDS-KC-main.spec
```

## Build Troubleshooting

### Common Issues

#### Missing Modules
**Error:** `ModuleNotFoundError` during runtime
**Solution:** Add missing modules to `hiddenimports` in the spec file

#### Missing Data Files
**Error:** Configuration or model files not found
**Solution:** Verify data file paths in the `datas` list

#### Large Executable Size
**Issue:** Executable is unexpectedly large
**Solution:** 
- Check if unnecessary files are being included
- Use `--exclude-module` for unused packages
- Consider standalone build without Npcap

#### Import Errors
**Error:** Import failures at runtime
**Solution:**
- Check Python path configuration
- Verify all dependencies are installed
- Add problematic modules to `hiddenimports`

### Debug Information

#### Enable Verbose Output
```bash
pyinstaller --clean --log-level DEBUG SCADA-IDS-KC-main.spec
```

#### Check Build Analysis
```bash
# View dependency analysis
cat build/SCADA-IDS-KC/Analysis-00.toc

# Check warnings
cat build/SCADA-IDS-KC/warn-SCADA-IDS-KC.txt
```

## Optimization Tips

### Reducing Executable Size
1. **Exclude Unused Modules:**
   ```python
   excludes = ['tkinter', 'matplotlib', 'scipy']
   ```

2. **Use UPX Compression:**
   ```bash
   pyinstaller --upx-dir=/path/to/upx SCADA-IDS-KC-main.spec
   ```

3. **Optimize Data Files:**
   - Include only necessary configuration files
   - Compress large data files
   - Use relative paths for runtime loading

### Improving Build Speed
1. **Use Build Cache:**
   ```bash
   pyinstaller --clean=false SCADA-IDS-KC-main.spec
   ```

2. **Parallel Processing:**
   ```bash
   pyinstaller --processes=4 SCADA-IDS-KC-main.spec
   ```

## Testing Built Executables

### Basic Functionality Tests
```bash
# Test version
.\dist\SCADA-IDS-KC.exe --cli --version

# Test help
.\dist\SCADA-IDS-KC.exe --help

# Test Npcap diagnostics
.\dist\SCADA-IDS-KC.exe --cli --diagnose-npcap
```

### Advanced Testing
```bash
# Test interface listing
.\dist\SCADA-IDS-KC.exe --cli --interfaces

# Test configuration loading
.\dist\SCADA-IDS-KC.exe --cli --status

# Test GUI mode (if display available)
.\dist\SCADA-IDS-KC.exe
```

## Integration with Build Scripts

### PowerShell Scripts
The PowerShell build scripts automatically:
- Change to packaging directory
- Run PyInstaller with proper parameters
- Handle build artifacts and cleanup
- Verify executable creation

### GitHub Actions
The CI/CD workflows:
- Use the same spec file for consistency
- Handle both build variants
- Upload build artifacts
- Run comprehensive testing

## Maintenance

### Updating Dependencies
When adding new Python dependencies:
1. Update `requirements.txt`
2. Test local build
3. Check for new hidden imports needed
4. Update spec file if necessary

### Modifying Data Files
When changing included files:
1. Update `datas` list in spec file
2. Test both build variants
3. Verify file accessibility at runtime
4. Update documentation

### Version Updates
For new releases:
1. Update version information in source
2. Test build process thoroughly
3. Verify all features work in built executable
4. Update build documentation if needed
