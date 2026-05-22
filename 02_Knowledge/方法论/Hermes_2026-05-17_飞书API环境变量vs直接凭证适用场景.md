# 飞书API两套认证方式的适用场景

**背景**
2026-05-17的AI热点推送12:00任务，飞书发送步骤失败，错误信息：`$FEISHU_APP_ID / $FEISHU_APP_SECRET 环境变量未设置`。但同时段其他任务的飞书发送却成功了。对比发现：成功的任务使用了直接硬编码凭证，失败的任务依赖环境变量。

**核心洞察**

## 两套认证方式对比

| 方式 | 凭证来源 | 适用场景 | 成功率 |
|------|---------|---------|--------|
| **环境变量法** | $FEISHU_APP_ID, $FEISHU_APP_SECRET | cron任务中通过shell脚本调用Python | ❌ 常失败（cron环境变量不继承） |
| **直接硬编码法** | Python脚本中写死APP_ID和APP_SECRET | execute_code中直接import requests调用 | ✅ 稳定 |

## 根因：cron环境的变量隔离

cron任务执行时，shell环境变量不会自动传递给execute_code的Python子进程。只有在execute_code的Python脚本中显式import os.environ获取，或在cron任务描述中显式export变量，才能使用环境变量。

某些Python脚本（如xhs_b_publish.py内部调用飞书API时）依赖$FEISHU_APP_ID，但execute_code子进程没有这个环境变量。

## wiki-platform-ops技能中的正确做法

wiki-platform-ops技能文档记录的是**netrc + credential.helper**方式（用于GitHub），飞书发送则使用**直接API调用**：

```python
# 飞书发送的正确方式（直接硬编码）
import requests, json

APP_ID = "cli_a96f4f328a785cd2"
APP_SECRET = "jYFMuuszh8g5h1bvb32Q1dcywimWG1TH"

# 获取 tenant_access_token
token_url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
r = requests.post(token_url, json={"app_id": APP_ID, "app_secret": APP_SECRET}, verify=False)
token = r.json()["tenant_access_token"]

# 发送消息
msg_url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id"
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=utf-8"}
payload = {
    "receive_id": "oc_1e92781cdf15f71fad7dcd8d5d386e76",
    "msg_type": "post",
    "content": json.dumps(post_content, ensure_ascii=False)
}
requests.post(msg_url, headers=headers, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"), verify=False)
```

## 判断方法

在cron任务的Python脚本中，不要依赖环境变量，直接在脚本顶层定义凭证常量。若凭证需要保密（如GitHub token），放在~/.netrc或环境配置文件（如~/.hermes/scripts/feishu_config.py）中，脚本import引用。

**对Jerry的意义**
避免飞书发送任务在cron环境中静默失败。如果飞书消息没有按时收到，首先检查任务是使用环境变量法还是直接凭证法，优先切换到直接凭证法。

**延伸思考**
这是一个典型的"开发环境vs生产环境"差异问题。execute_code直接运行时环境变量正常，但cron调度时代码运行在最小化的shell环境。解决方案：要么把环境变量写入配置文件让Python显式读取，要么直接在脚本中写死（适合内部工具）。

**标签**：Hermes × 飞书API × 环境变量 × cron环境 × 凭证管理 × 运维
