"""Local UI verification without exposing account passwords in output."""
from pathlib import Path
from playwright.sync_api import sync_playwright

root = Path(__file__).resolve().parents[1]
out = root / 'test-results'
out.mkdir(exist_ok=True)
credentials = dict(line.split(': ', 1) for line in (root / 'private/accounts.txt').read_text().splitlines() if ': ' in line and line.split(': ', 1)[0] in ('admin', 'viewer'))
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1440, 'height': 1000})
    page.goto('http://127.0.0.1:8502')
    page.get_by_role('button', name='登录', exact=True).wait_for()
    page.screenshot(path=str(out / 'login.png'), full_page=True)
    page.get_by_label('账号', exact=True).fill('viewer')
    page.get_by_label('密码', exact=True).fill(credentials['viewer'])
    page.get_by_role('button', name='登录', exact=True).click()
    page.get_by_role('button', name='退出登录').wait_for()
    page.wait_for_timeout(1500)
    page.get_by_role('heading', name='🌌 工作空间').wait_for()
    page.get_by_role('link', name='算法题库', exact=True).wait_for()
    page.screenshot(path=str(out / 'viewer.png'), full_page=True)
    assert page.get_by_role('button', name='保存记录').count() == 0
    print('Viewer login and write-button isolation: OK')
    page.get_by_role('button', name='退出登录').click()
    page.get_by_role('button', name='登录', exact=True).wait_for()
    page.get_by_label('账号', exact=True).fill('admin')
    page.get_by_label('密码', exact=True).fill(credentials['admin'])
    page.get_by_role('button', name='登录', exact=True).click()
    page.get_by_role('button', name='退出登录').wait_for()
    page.wait_for_timeout(1500)
    page.screenshot(path=str(out / 'admin.png'), full_page=True)
    print('Admin login: OK')
    page.get_by_role('link', name='算法题库', exact=True).click()
    page.get_by_role('heading', name='🧩 算法题库').wait_for()
    print('Chinese navigation and page switching: OK')
    page.get_by_role('link', name='工作空间', exact=True).click()
    page.get_by_role('heading', name='🌌 工作空间').wait_for()
    page.set_viewport_size({'width': 390, 'height': 844})
    page.wait_for_timeout(500)
    page.screenshot(path=str(out / 'mobile.png'), full_page=True)
    print('Mobile horizontal overflow:', page.evaluate('document.documentElement.scrollWidth > window.innerWidth'))
    remote = browser.new_page()
    remote.goto('https://ai-workbench-fpyr2gqpk8zdfrdwmuh6dg.streamlit.app/', wait_until='domcontentloaded', timeout=60000)
    remote.wait_for_timeout(8000)
    print('Original site title:', remote.title())
    body = remote.locator('body').inner_text()
    for marker in ['Oh no.', 'This app has gone to sleep', 'OperationalError', 'Error', 'app not found', '账号', '管理']:
        if marker.casefold() in body.casefold():
            print('Original site marker:', marker)
    browser.close()
