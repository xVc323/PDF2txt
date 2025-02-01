# hook-google.generativeai.py
from PyInstaller.utils.hooks import collect_all

# Collect everything from google.generativeai
datas, binaries, hiddenimports = collect_all('google.generativeai')

# Add additional dependencies
hiddenimports.extend([
    'google.auth',
    'google.auth.transport.requests',
    'google.oauth2.credentials',
    'google.api_core',
    'google.api_core.operations_v1',
    'google.api_core.gapic_v1',
    'google.api_core.retry',
])