# -*- mode: python ; coding: utf-8 -*-

import PyInstaller.config

# Base path configuration
BASE_PATH = "C:\\Users\\Arthu\\Documents\\GitHub\\PhotoOrganizer"

PyInstaller.config.CONF['distpath'] = f"{BASE_PATH}\\Distribution\\dist"
PyInstaller.config.CONF['workpath'] = f"{BASE_PATH}\\Distribution\\build"


a = Analysis(
    [f'{BASE_PATH}\\src\\gui.py'],
    pathex=[],
    binaries=[],
    datas=[
        (f'{BASE_PATH}\\src\\assets\\icons\\Photo Organizer icon.ico', 'assets/icons'),
        (f'{BASE_PATH}\\src\\assets\\LastUsedSource.txt', 'assets'),
        (f'{BASE_PATH}\\src\\assets\\LastUseddestination.txt', 'assets'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Photo Organizer',
    icon=f'{BASE_PATH}\\src\\assets\\icons\\Photo Organizer icon.ico',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
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
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Photo Organizer',
)
