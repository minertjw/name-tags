# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src/nametags/__main__.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src/nametags/assets', 'nametags/assets'),
        ('src/nametags/web/static', 'nametags/web/static'),
        ('src/nametags/web/templates', 'nametags/web/templates'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[], # Scripts to run before compiled application starts
    excludes=[
        "altgraph",
        "colorama",
        "iniconfig",
        "packaging",
        "pefile",
        "pluggy",
        "pygments",
        "pyinstaller",
        "pyinstaller-hooks-contrib",
        "pytest",
        "pywin32-ctypes",
        "setuptools",
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True, # True in onedir builds
    name='nametags',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True, # Compress binaries if UPX is installed
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    name='nametags',
    strip=False,
    upx=True,
)
