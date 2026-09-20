# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src/nametags/__main__.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src/nametags/assets', 'nametags/assets'),
        ('src/nametags/web/static', 'nametags/web/static'),
        ('src/nametags/web/templates', 'nametags/web/templates')
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
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
    a.binaries,
    a.datas,
    [],
    name='nametags-onefile',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
