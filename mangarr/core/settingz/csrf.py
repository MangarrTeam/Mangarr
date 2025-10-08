from .config import CONFIG

origins = CONFIG.get('Networking', 'csrf_trusted_origins', 'localhost:80,127.0.0.1:80', description='List of CSRF thursted origins separated by comma (",")').split(',')
CSRF_TRUSTED_ORIGINS = [
    f'http://{origin}' if not origin.startswith(('http://', 'https://')) else origin
    for origin in origins
] + [
    f'https://{origin}' if not origin.startswith(('http://', 'https://')) else origin
    for origin in origins
] + [
    origin
    for origin in origins if origin.startswith(('http://', 'https://'))
]