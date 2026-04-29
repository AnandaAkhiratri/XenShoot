# XenShoot - Build Instructions

## Building Executable (.exe)

### Requirements:
- Python 3.8+
- PyInstaller
- All dependencies installed

### Build Steps:

1. **Install PyInstaller:**
```bash
pip install pyinstaller
```

2. **Build executable:**
```bash
pyinstaller XenShoot.spec --clean
```

3. **Find output:**
```
dist/XenShoot.exe  (~77 MB single file)
```

### Spec File Details:

The `XenShoot.spec` file configures:
- ✅ Single-file executable
- ✅ No console window (GUI only)
- ✅ Includes all source files (`src/`)
- ✅ Includes Logo assets
- ✅ Custom app icon
- ✅ UPX compression enabled
- ✅ All hidden imports (PyQt5, boto3, requests, PIL)

### Distribution:

**Option 1: Direct EXE**
- Share `dist/XenShoot.exe`
- Users run directly (portable, no installation)
- All dependencies bundled

**Option 2: Installer (Optional)**
- Use Inno Setup or NSIS
- Create Windows installer
- Add desktop shortcut
- Add to Start Menu
- Auto-start option

### Testing Built EXE:

1. Copy `XenShoot.exe` to clean folder
2. Run executable
3. Test all features:
   - Screenshot capture
   - Annotation tools
   - Upload to Backblaze
   - API connection to xenshot.cloud
   - System tray icon
   - Global hotkeys

### Build Notes:

**Warnings (can ignore):**
- `Hidden import 'keyboard' not found` - OK, bundled differently
- `Hidden import "sip" not found` - OK, PyQt5 includes this

**File Size:**
- Single EXE: ~77 MB
- Includes Python runtime + all dependencies
- No external files needed

### Optimizations:

**Reduce size (optional):**
```spec
# In XenShoot.spec
upx=True,           # Already enabled
excludes=['tkinter', 'matplotlib'],  # If not needed
```

**Add version info:**
```python
# In .spec file, add before EXE:
version = 'version.txt'  # Create version.txt with metadata
```

### Troubleshooting:

**"Failed to execute script":**
- Check all files in `datas` exist
- Verify icon.ico exists
- Run with console first: `console=True` in .spec

**"Module not found":**
- Add to `hiddenimports` in .spec
- Rebuild with `--clean`

**Large file size:**
- Normal for single-file EXE
- Includes entire Python + dependencies
- Alternative: use `--onedir` (creates folder)

### Creating Installer (Inno Setup):

1. Download Inno Setup: https://jrsoftware.org/isdl.php
2. Create `installer.iss`:

```iss
[Setup]
AppName=XenShoot
AppVersion=1.0.0
DefaultDirName={pf}\XenShoot
DefaultGroupName=XenShoot
OutputDir=installer
OutputBaseFilename=XenShoot-Setup
Compression=lzma
SolidCompression=yes

[Files]
Source: "dist\XenShoot.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\XenShoot"; Filename: "{app}\XenShoot.exe"
Name: "{userdesktop}\XenShoot"; Filename: "{app}\XenShoot.exe"

[Run]
Filename: "{app}\XenShoot.exe"; Description: "Launch XenShoot"; Flags: nowait postinstall skipifsilent
```

3. Compile with Inno Setup

### Distribution Checklist:

- [ ] Test EXE on clean Windows machine
- [ ] Verify all features work
- [ ] Test upload to Backblaze
- [ ] Test API connection to xenshot.cloud
- [ ] Create README for users
- [ ] (Optional) Code sign certificate
- [ ] (Optional) Create installer
- [ ] Upload to GitHub Releases

### GitHub Release:

```bash
# Tag version
git tag v1.0.0
git push origin v1.0.0

# Upload to GitHub Releases
# - Go to: https://github.com/AnandaAkhiratri/XenShoot/releases
# - Create new release
# - Upload XenShoot.exe
# - Add release notes
```

---

**Build Output:** `dist/XenShoot.exe`
**Size:** ~77 MB
**Type:** Standalone executable (no installation needed)
