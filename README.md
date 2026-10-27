# AI Workbench

一个带管理员 / 只读账号的 Streamlit 学习、项目与科研工作台。

## 本地运行（Windows）

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe tools/create_accounts.py
.\.venv\Scripts\python.exe -m streamlit run app.py
```

`tools/create_accounts.py` 为 admin / viewer 生成随机密码，只在本机 `private/accounts.txt` 保存明文，在 `.streamlit/secrets.toml` 保存 PBKDF2 密码哈希。已有账号不会被覆盖。默认登录有效期 8 小时；修改账号密码哈希会使旧会话失效。失败登录有进程内共享冷却限制；多实例部署需使用统一身份服务 / 共享限流存储。

不配置 DB_URI 时使用本地 SQLite；现有 DB_URI 不会被账号生成工具改写。测试临时切换本地数据库可使用：

```powershell
$env:WORKBENCH_DB_URI='sqlite:///E:/AIWorkbench/private/preview.db'
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1 --server.port 8502
```

## 权限与功能

| 功能 | 管理员 | 浏览账号 |
| --- | --- | --- |
| 登录后查看各数据模块、搜索和筛选 | ✓ | ✓ |
| 新增、编辑、确认后删除 | ✓ | — |
| CSV 导出、全量 ZIP 数据备份 | ✓ | — |
| 自带 API Key 的模型沙箱 | ✓ | — |

所有页面入口均校验登录；读取与写入服务再次校验权限。匿名请求不加载数据。模型请求不跟随重定向，拒绝本机、内网及非 HTTPS 地址，不展示上游错误正文。浏览账号可以阅读并手动复制可见数据；如某些数据不应被其阅读，应另外划分公开字段。

首页提供指标、待办状态和未来 14 天 / 已逾期提醒。课程支持百分制与等级成绩，百分制加权均分只统计有效百分制课程，不宣称是学校官方绩点。旧数据库仅按需补充待办 status 列，保留现有记录。生产数据库建议另设独立的最小权限连接账号，并在 Supabase 检查 API 暴露与 RLS；应用登录不能代替数据库自身的访问控制。

## 更新原 Streamlit 网址

1. 保持 Streamlit Cloud 原有应用和自定义域名，核对其连接仓库 `re7-dev/AI-Workbench`、分支 `main`、入口 `app.py`。
2. 进入原应用 Settings → Secrets，保留正确的 DB_URI，加入本机 `.streamlit/secrets.toml` 中的 `[auth.users.admin]` 和 `[auth.users.viewer]` 两段配置。真实 Secrets、密码、数据库和 private 目录不可上传 GitHub。
3. 如数据库地址无法解析，登录 Supabase 控制台检查项目是否暂停 / 已删除、连接主机是否变更。从 Connect 复制可用连接字符串；根据部署环境选用受支持的 pooler，并启用 SSL。不要把密码发到聊天或仓库。
4. 原应用 Reboot，查看 Logs。缺少账号时系统会停止并提示配置，不会开放匿名访问；错误不会向访客输出数据库 URI。
5. 分别用管理员、浏览账号登录，验证浏览账号无编辑 / 删除 / 导出 / 模型调用功能。

Python 依赖已固定为本机实际测试版本。Streamlit Cloud 需要使用这些依赖支持的 Python（建议 3.12 或 3.14）；若原部署环境过旧，在应用设置中调整。

## 测试

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

自动测试使用独立临时 SQLite，不触碰生产数据。`tools/check_deployment.py` 仅检查原网址 HTTP、DNS 和数据库 SELECT 1，不输出凭据。`tools/browser_check.py` 对本机 8502 端口执行管理员 / 浏览登录及截图，截图保存在不上传的 test-results 目录。
