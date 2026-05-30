# BHR 小红书发布 WebSocket 连接修复

**背景**
2026-05-25 小红书梵高图文流水线执行时，BHR（浏览器自动化发布）持续失败，错误信息为"无法获取 WS URL"。根本原因分析发现，`get_ws_url()` 函数依赖的日志文件 `/tmp/chrome_xhs.log` 不存在，而 Chrome 实际运行在 9543 端口，CDP WebSocket 正常可用。

**核心洞察**
BHR 的 `get_ws_url()` 实现有两种模式：
1. **日志读取模式**：从 `/tmp/chrome_xhs.log` 读取 Chrome DevTools Protocol 地址 → 这个文件在自动化环境中不存在
2. **CDP 直接探测模式**：直接 curl `http://127.0.0.1:9543/json` 获取 WebSocket URL → 这是实际工作的方式

问题出在脚本优先尝试日志模式，失败后没有回退到 CDP 直接探测。

**修复方案**
将 `xhs_vangogh_gen.py` 中的 BHR 部分替换为：
```python
import requests
resp = requests.get("http://127.0.0.1:9543/json", timeout=5)
ws_url = resp.json()[0]["webSocketDebuggerUrl"]
```

**对Jerry的意义**
小红书梵高图文日更流水线已高度标准化（每日3个批次，每批10张插画），BHR 发布失败意味着内容无法自动触达用户，只能手动发布。修复此问题可实现全自动化。

**延伸思考**
这个模式也适用于其他依赖 Chrome CDP 的自动化场景（browser skill、网页抓取等）。核心原则：日志文件不可靠时，直接探测端口比读文件更稳定。

**标签**：Hermes × 小红书 × BHR × Chrome CDP × 自动化修复