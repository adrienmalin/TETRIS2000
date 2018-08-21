# -*- mode: python -*-

block_cipher = None


a = Analysis(['TETRIS2000.py'],
             pathex=[],
             binaries=[],
             datas=[
             ("backgrounds/*", "backgrounds"),
             ("fonts/*.ttf", "fonts"),
             ("fonts/*.otf", "fonts"),
             ("icons/*.ico", "icons"),
             ("icons/splash_screen.png", "icons"),
             ("locale/*.qm", "locale"),
             ("musics/*.mp3", "musics"),
             ("sfx/*.wav", "sfx")
             ],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=["PyQt4", "PySide", "PySide2"],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='TETRIS2000',
          debug=False,
          strip=False,
          upx=False,
          console=False,
          icon='icons\icon.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=False,
               name='TETRIS2000')