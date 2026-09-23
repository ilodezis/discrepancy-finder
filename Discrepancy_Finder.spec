# -*- mode: python ; coding: utf-8 -*-
# Build: pyinstaller Discrepancy_Finder.spec
# Windows -> dist/Discrepancy_Finder.exe, macOS -> dist/Discrepancy Finder.app
import sys
from pathlib import Path

base_dir = Path(SPECPATH).resolve()
icon_file = str(base_dir / "assets" / "icons" / "icons8-yandex-international-240.ico")

datas = [
    (icon_file, "assets/icons"),
    (str(base_dir / "assets" / "fonts" / "Inter-VariableFont_opsz,wght.ttf"), "assets/fonts"),
    (str(base_dir / "i18n"), "i18n"),
    (str(base_dir / "config.yaml"), "."),
    (str(base_dir / "style.qss"), "."),
]

a = Analysis(
    [str(base_dir / "main.py")],
    pathex=[str(base_dir)],
    datas=datas,
    hiddenimports=["openpyxl", "xlrd", "yaml"],
    excludes=["tkinter", "matplotlib", "IPython", "pytest"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="Discrepancy_Finder",
    debug=False,
    strip=False,
    upx=True,
    console=False,
    icon=icon_file,
)

if sys.platform == "darwin":
    app = BUNDLE(
        exe,
        name="Discrepancy Finder.app",
        icon=None,
        bundle_identifier="com.ilodezis.discrepancyfinder",
    )
