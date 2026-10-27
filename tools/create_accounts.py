"""Generate local credentials without putting passwords in source control."""
import hashlib
from pathlib import Path
import secrets
import tomllib


def main():
    root = Path(__file__).resolve().parents[1]
    target = root / '.streamlit' / 'secrets.toml'
    existing = target.read_text(encoding='utf-8') if target.exists() else ''
    if tomllib.loads(existing).get('auth'):
        raise SystemExit('Accounts already configured; edit Secrets explicitly to rotate credentials.')
    folder = root / 'private'
    folder.mkdir(exist_ok=True)
    credentials = []
    additions = []
    for username, role in [('admin', 'admin'), ('viewer', 'viewer')]:
        password = secrets.token_urlsafe(18)
        salt = secrets.token_hex(16)
        digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 600000).hex()
        additions.append(f'\n[auth.users.{username}]\nrole = "{role}"\npassword_hash = "pbkdf2_sha256$600000${salt}${digest}"\n')
        credentials.append(f'{username}: {password}')
    # Write credentials first; never overwrite a previous credential file.
    with (folder / 'accounts.txt').open('x', encoding='utf-8') as file:
        file.write('\n'.join(credentials) + '\n')
    target.write_text(existing + '\n'.join(additions), encoding='utf-8')
    print('Accounts created. Credentials: private/accounts.txt. Do not upload this folder.')


if __name__ == '__main__':
    main()
