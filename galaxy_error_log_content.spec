# -*- mode: python -*-

block_cipher = None
requests_files = Tree(r'C:\Python35\Lib\site-packages\requests', prefix='requests')


a = Analysis(['galaxy_error_log_content.py'],
             pathex=['C:\\simon_files_compilation_zone\\galaxy_error_log'],
             binaries=None,
             datas=None,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          requests_files,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='galaxy_error_log_content',
          debug=False,
          strip=False,
          upx=True,
          console=False )
