# -*- mode: python -*-

block_cipher = None


a = Analysis(['Tetris2000.py'],
             pathex=[],
             binaries=[],
             datas=[(r'data\backgrounds\*.jpg', r'data\backgrounds'),
                    (r'data\fonts\*.ttf', r'data\fonts'),
                    (r'data\fonts\*.otf', r'data\fonts'),
                    (r'data\icons\icon.ico', r'data\icons'),
                    (r'data\locale\*.qm', r'data\locale'),
                    (r'data\sounds\*.wav', r'data\sounds'),
                    (r'data\sounds\*.mp3', r'data\sounds')],
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
          name='Tetris 2000',
          debug=False,
          strip=False,
          upx=False,
          console=False ,
          icon='data\icons\icon.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=False,
               name='Tetris 2000')
