# -*- mode: python ; coding: utf-8 -*-

package_version = "0.3.0"

a = Analysis(
    ['publish.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['paramiko'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='publisher',
          debug=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=True )

