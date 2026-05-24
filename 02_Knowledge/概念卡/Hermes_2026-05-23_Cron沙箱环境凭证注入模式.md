# Cron沙箱环境凭证注入的三种模式

**背景**
Hermes cron任务运行在独立的沙箱环境中，该环境没有继承用户终端的环境变量（如 FEISHU_APP_ID / FEISHU_APP_SECRET），导致飞书凭证相关的 skill（如 `feishu-env-credentials`）在 cron 定时任务中调用会失败。5月23日的推送日报中多处记录了这一问题。

**核心洞察**
凭证注入有三种可行模式，根据场景选择：

**模式一：直接硬编码凭证（不推荐用于敏感环境）**
适用于一次性脚本或内部工具，直接在代码中写入凭证：
```python
APP_ID = "cli_a96f4f328a785cd2"
APP_SECRET = "jYFMuuszh8g5h1bvb32Q1dcywimWG1TH"
```

**模式二：从本地文件读取（推荐用于cron）**
凭证不写在代码里，而是写在配置文件中，运行时读取：
```python
# 凭证存储在 ~/.hermes/skills/feishu-env-credentials/token.txt
# 或存储在 Python 文件同级目录的 config.py 中
from pathlib import Path
token_file = Path.home() / ".hermes/skills/feishu-env-credentials/token.txt"
```

**模式三：环境变量注入（适用于launchd/launchctl托管的服务）**
通过 launchd plist 的 EnvironmentVariables 注入：
```xml
<key>EnvironmentVariables</key>
<dict>
    <key>FEISHU_APP_ID</key>
    <string>cli_a96f4f328a785cd2</string>
</dict>
```

**问题诊断**
cron任务中飞书凭证调用失败的典型错误：
```
feishu_env_credentials not found / skill not loaded
```
原因：skill是交互式环境下通过工具注入的，cron沙箱不加载skills。

**对Jerry的意义**
在写任何 cron 定时任务时，涉及飞书 API 调用的任务必须使用模式二（文件读取），不要依赖 skill 注入。已知的飞书凭证：
- APP_ID: cli_a96f4f328a785cd2
- APP_SECRET: jYFMuuszh8g5h1bvb32Q1dcywimWG1TH

**延伸思考**
对于高频使用的凭证，可以考虑统一写入 ~/.netrc 或专用凭证配置文件，避免散落在多个脚本中。GitHub PAT 就是通过 ~/.netrc + git credential.helper 统一管理凭证的典范。

**标签**：Hermes × Cron × 飞书API × 凭证管理 × 环境变量