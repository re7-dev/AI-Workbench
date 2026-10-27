"""Read-only diagnostics; never print credentials or exception connection strings."""
from pathlib import Path
import socket
import tomllib
from urllib.parse import urlparse
import requests
from sqlalchemy import create_engine, text

root = Path(__file__).resolve().parents[1]
url = 'https://ai-workbench-fpyr2gqpk8zdfrdwmuh6dg.streamlit.app/'
try:
    response = requests.get(url, timeout=30)
    print('Website HTTP:', response.status_code)
    print('Final host:', urlparse(response.url).hostname)
    print('Contains Streamlit login:', 'auth' in urlparse(response.url).hostname)
except Exception as exc:
    print('Website check failed:', type(exc).__name__)
config = tomllib.loads((root / '.streamlit/secrets.toml').read_text(encoding='utf-8'))
uri = config.get('DB_URI', '')
try:
    parsed = urlparse(uri)
    socket.getaddrinfo(parsed.hostname, parsed.port or 5432)
    print('Database DNS: OK')
except OSError:
    print('Database DNS: FAILED')
try:
    engine = create_engine(uri, connect_args={'connect_timeout': 10})
    with engine.connect() as conn:
        print('Database SELECT 1:', conn.execute(text('SELECT 1')).scalar())
    engine.dispose()
except Exception as exc:
    print('Database connection failed:', type(exc).__name__)
