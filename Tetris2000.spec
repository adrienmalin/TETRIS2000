# -*- mode: python -*-

block_cipher = None


a = Analysis(['Tetris2000/Tetris2000.py'],
             pathex=[],
             binaries=[],
             datas=[('Tetris2000/data/backgrounds\*.jpg', 'data/backgrounds'),
                    ('Tetris2000/data/fonts\*.ttf', 'data/fonts'),
                    ('Tetris2000/data/fonts\*.otf', 'data/fonts'),
                    ('Tetris2000/data/icons\icon.ico', 'data/icons'),
                    ('Tetris2000/data/locale\*.qm', 'data/locale'),
                    ('Tetris2000/data/sounds\*.wav', 'data/sounds'),
                    ('Tetris2000/data/sounds\*.mp3', 'data/sounds')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[r'.\use_lib.py'],
             excludes=["PySide2"],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='Tetris2000',
          debug=False,
          strip=False,
          upx=False,
          console=False ,
          icon='Tetris2000/data/icons/icon.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=False,
               name='Tetris2000')
