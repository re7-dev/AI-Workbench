import ipaddress
import socket
from urllib.parse import urlparse
import requests
from core.auth import require_access


def validate_api_url(url):
    parsed = urlparse(url)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or parsed.port not in (None, 443):
        raise ValueError('仅支持公共 HTTPS API 地址（443 端口）')
    addresses = socket.getaddrinfo(parsed.hostname, 443, type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(address[4][0]).is_global for address in addresses):
        raise ValueError('不允许访问本机或内网地址')


def call_llm_api(api_url, api_key, model_name, prompt, temperature=0.7):
    require_access(admin=True)
    try:
        validate_api_url(api_url)
        if not model_name.strip():
            return None, '请填写模型名称'
        response = requests.post(api_url, headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}, json={'model': model_name, 'messages': [{'role': 'user', 'content': prompt}], 'temperature': temperature}, timeout=(10, 60), allow_redirects=False)
        if response.status_code != 200:
            return None, f'API 请求失败（HTTP {response.status_code}），请检查配置。'
        return response.json()['choices'][0]['message']['content'], None
    except (ValueError, OSError):
        return None, 'API 地址无效或无法解析，请使用公共 HTTPS 地址。'
    except (requests.RequestException, KeyError, IndexError, TypeError):
        return None, '请求失败或响应格式不兼容，请检查服务与配置。'
