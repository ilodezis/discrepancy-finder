# -*- mode: python ; coding: utf-8 -*-
import os
from pathlib import Path

# Define paths
base_dir = Path('c:/Users/ilode/OneDrive/Documents/Projects/discrepancy-finder').resolve()
icon_file = str(base_dir / 'assets' / 'icons' / 'icons8-yandex-international-240.ico')
font_file = str(base_dir / 'assets' / 'fonts' / 'Inter-VariableFont_opsz,wght.ttf')
i18n_dir = str(base_dir / 'i18n')
config_file = str(base_dir / 'config.yaml')
style_file = str(base_dir / 'style.qss')

# Add files to datas
datas = [
    (icon_file, 'assets/icons'),
    (font_file, 'assets/fonts'),
    (i18n_dir, 'i18n'),
    (config_file, '.'),
    (style_file, '.'),
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=['PyQt5.QtWidgets', 'pandas', 'openpyxl', 'yaml'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Discrepancy_Finder',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,  # Используем абсолютный путь к иконке
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Discrepancy_Finder'
)
