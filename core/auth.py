import hashlib
import hmac
import secrets
import time
import threading
from collections import OrderedDict
import streamlit as st


def hash_password(password):
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 600000).hex()
    return f'pbkdf2_sha256$600000${salt}${digest}'


def verify_password(password, encoded):
    try:
        algorithm, iterations, salt, expected = encoded.split('$')
        if algorithm != 'pbkdf2_sha256' or not 100000 <= int(iterations) <= 2000000:
            return False
        actual = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), int(iterations)).hex()
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError, AttributeError):
        return False


def accounts():
    try:
        return st.secrets.get('auth', {}).get('users', {})
    except (FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
        return {}


@st.cache_resource
def login_attempts():
    # Shared across browser sessions in this process; reconnecting does not reset it.
    return OrderedDict(), threading.Lock()


def authenticate(username, password):
    attempts, lock = login_attempts()
    key = hashlib.sha256(username.casefold().encode()).hexdigest()
    with lock:
        failures, retry_after = attempts.get(key, (0, 0))
        if time.time() < retry_after:
            return None
        account = accounts().get(username, {})
        if verify_password(password, account.get('password_hash', '')) and account.get('role') in ('admin', 'viewer'):
            attempts.pop(key, None)
            return account
        # Bounded memory, and a shared account cooldown after repeated failures.
        attempts[key] = (failures + 1, time.time() + min(60, 2 ** min(failures, 6)))
        attempts.move_to_end(key)
        while len(attempts) > 10000:
            attempts.popitem(last=False)
        return None


def role():
    identity = st.session_state.get('_identity', {})
    if time.time() - identity.get('issued', 0) > 8 * 3600:
        return None
    account = accounts().get(identity.get('username', ''), {})
    if not hmac.compare_digest(str(account.get('password_hash', '')), identity.get('version', '!')):
        return None
    value = account.get('role')
    return value if value in ('admin', 'viewer') else None


def require_access(admin=False):
    current = role()
    if current is None or (admin and current != 'admin'):
        raise PermissionError('当前账号无权执行此操作')


def login_gate():
    if role():
        st.sidebar.caption(f"账号：{st.session_state['_identity']['username']} · {'管理员' if role() == 'admin' else '仅浏览'}")
        if st.sidebar.button('退出登录', use_container_width=True):
            st.session_state.clear()
            st.rerun()
        return
    st.title('AI Workbench')
    st.caption('学习、工程与研究，一个专注的工作空间。')
    if not accounts():
        st.error('尚未配置登录账号。请管理员在 Secrets 中配置账号后重启应用。')
        st.stop()
    with st.form('login'):
        username = st.text_input('账号', max_chars=80)
        password = st.text_input('密码', type='password', max_chars=256)
        submit = st.form_submit_button('登录', type='primary', use_container_width=True)
    if submit:
        if time.time() < st.session_state.get('_retry_after', 0):
            st.error('尝试过于频繁，请稍后再试。')
        else:
            account = authenticate(username.strip(), password)
            if account:
                st.session_state.clear()
                st.session_state['_identity'] = dict(username=username.strip(), issued=time.time(), version=account['password_hash'])
                st.rerun()
            else:
                failures = st.session_state.get('_failures', 0) + 1
                st.session_state['_failures'] = failures
                st.session_state['_retry_after'] = time.time() + min(60, 2 ** min(failures, 6))
                st.error('账号或密码错误。')
    st.stop()
