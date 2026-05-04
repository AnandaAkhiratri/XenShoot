# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src/Logo', 'src/Logo'),
        ('src/fonts', 'src/fonts'),
    ],
    hiddenimports=[
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'PyQt5.QtSvg',
        'pynput',
        'pynput.keyboard',
        'pynput.mouse',
        'pynput.keyboard._win32',
        'pynput.mouse._win32',
        'requests',
        'boto3',
        'botocore',
        'botocore.endpoint',
        'botocore.parsers',
        'botocore.serialize',
        'botocore.signers',
        'PIL',
        'PIL.Image',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Dev tools — not needed in production
        'dev', 'watchdog', 'watchdog.observers', 'watchdog.events',
        # Unused PyQt5 modules
        'PyQt5.QtNetwork', 'PyQt5.QtWebEngineWidgets', 'PyQt5.QtWebEngine',
        'PyQt5.QtMultimedia', 'PyQt5.QtSql', 'PyQt5.QtBluetooth',
        'PyQt5.QtLocation', 'PyQt5.Qt3DCore', 'PyQt5.QtXml',
        'PyQt5.QtTest', 'PyQt5.QtOpenGL', 'PyQt5.QtDesigner',
        # Unused stdlib (safe to exclude)
        'tkinter', 'turtle', 'curses', 'lib2to3',
        # Unused boto3 services (keep only s3)
        'boto3.dynamodb', 'boto3.ec2', 'boto3.glacier',
        # Unused PIL plugins
        'PIL.FitsImagePlugin', 'PIL.FpxImagePlugin', 'PIL.MicImagePlugin',
        'PIL.SgiImagePlugin', 'PIL.SpiderImagePlugin', 'PIL.WmfImagePlugin',
        # Other unused
        'numpy', 'pandas', 'matplotlib', 'scipy', 'IPython',
        'pygments', 'docutils', 'sphinx',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='KShot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
)
