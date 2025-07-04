# -*- mode: python ; coding: utf-8 -*-

# Devopin Backend PyInstaller Build Specification
# This file tells PyInstaller how to build your application

import os

# Get dynamic naming dari environment (untuk CI/CD)
platform = os.environ.get('BUILD_PLATFORM', 'linux')
arch = os.environ.get('BUILD_ARCH', 'amd64')
exe_name = f'devopin-backend-{platform}-{arch}'

block_cipher = None

a = Analysis(
    ['app/main.py'],  # 🎯 Entry point aplikasi kamu
    pathex=[],
    binaries=[],
    datas=[
        # 🎯 Include static files yang dibutuhkan aplikasi
        #('app/templates', 'templates'),     # Jika ada templates
        #('app/static', 'static'),           # Jika ada static files
        #('devopin.db', '.'),                # Include database file
        # ('config.yaml.example', '.'),     # Include config template
    ],
    hiddenimports=[
        # 🎯 Core packages dari requirements.txt
        'nicegui',
        'nicegui.elements',
        'nicegui.events',
        'nicegui.ui',
        'fastapi',
        'fastapi.responses',
        'fastapi.staticfiles',
        'fastapi.middleware',
        'fastapi.middleware.cors',
        'sqlalchemy',
        'sqlalchemy.dialects.sqlite',
        'sqlalchemy.orm',
        'sqlalchemy.ext.declarative',
        'alembic',
        'alembic.runtime',
        'alembic.script',
        'alembic.config',
        'argon2',
        'argon2.exceptions',
        'pydantic',
        'pydantic.fields',
        'pydantic_core',
        'uvicorn',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.websockets',
        'uvicorn.lifespan',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.logging',
        'starlette',
        'starlette.applications',
        'starlette.middleware',
        'starlette.routing',
        'starlette.responses',
        
        # 🎯 Socket.IO & WebSocket support
        'python_socketio',
        'python_engineio',
        'websockets',
        'simple_websocket',
        'wsproto',
        
        # 🎯 HTTP & networking
        'httpx',
        'httpcore',
        'h11',
        'httptools',
        'aiohttp',
        'aiosignal',
        'frozenlist',
        'multidict',
        'yarl',
        'aiohappyeyeballs',
        'propcache',
        
        # 🎯 File handling & async
        'aiofiles',
        'anyio',
        'sniffio',
        'uvloop',
        'watchfiles',
        
        # 🎯 Templating & markup
        'jinja2',
        'markupsafe',
        'markdown2',
        'pygments',
        
        # 🎯 Data serialization
        'orjson',
        'pyyaml',
        'python_multipart',
        
        # 🎯 Utility packages
        'python_dotenv',
        'requests',
        'urllib3',
        'certifi',
        'idna',
        'charset_normalizer',
        'click',
        'colorama',
        'packaging',
        'typing_extensions',
        'typing_inspection',
        
        # 🎯 NiceGUI specific
        'vbuild',
        'pscript',
        'wait_for2',
        'bidict',
        'ifaddr',
        
        # 🎯 Standard library yang sering bermasalah
        'contextlib',
        'json',
        'sqlite3',
        'datetime',
        'typing',
        'pathlib',
        'os',
        'sys',
        'asyncio',
        'threading',
        'multiprocessing',
        'subprocess',
        'tempfile',
        'shutil',
        'glob',
        'itertools',
        'functools',
        'collections',
        'base64',
        'hashlib',
        'hmac',
        'secrets',
        'uuid',
        'time',
        're',
        'weakref',
        'copy',
        'pickle',
        'gzip',
        'zipfile',
        'tarfile',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 🎯 Exclude packages yang tidak dibutuhkan untuk mengurangi size
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'tkinter',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=exe_name,
    debug=False,                          # Set True untuk debugging
    bootloader_ignore_signals=False,
    strip=False,                          # Strip symbols untuk mengurangi size
    upx=True,                            # Compress dengan UPX (jika installed)
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,                        # True = show console, False = hide console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='app/static/icon.ico',        # Uncomment jika ada icon
)

# 🎯 Optional: Create distribution directory structure
# coll = COLLECT(
#     exe,
#     a.binaries,
#     a.zipfiles,
#     a.datas,
#     strip=False,
#     upx=True,
#     upx_exclude=[],
#     name='devopin-backend'
# )