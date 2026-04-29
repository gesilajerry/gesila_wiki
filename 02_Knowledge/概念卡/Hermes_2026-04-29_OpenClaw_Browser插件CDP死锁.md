# OpenClaw Gateway CDP Browser 插件死锁

**背景**
OpenClaw Gateway（2026.4.25+ 版本）在启动后进程 PID 存在、端口 18789 监听，但所有 HTTP 请求超时（30s+），`openclaw status` 等命令也全部超时。进程 CPU 为 0%，日志不写入或写入极慢。

**核心洞察**
根因是 browser 插件的 CDP（Chrome DevTools Protocol）初始化阶段卡死 gateway。进程并未崩溃，而是挂在 CDP 连接上不响应 HTTP。Dev 模式（`OPENCLAW_PROFILE=dev`）因 `skipBootstrap: true` 能正常启动，说明问题确实在 bootstrap 阶段的 browser 插件初始化。

**诊断判断**
```
curl http://localhost:18789 → 连接超时（而非 connection refused）
ps aux | grep openclaw → 进程存在，CPU 0%
kill -USR2 <pid> → 日志缓冲区刷新后可见最后状态
```
满足以上三点即基本确认是 browser 插件 CDP 死锁。

**修复方法**
```python
import json
with open('/Users/mac/.openclaw/openclaw.json') as f:
    d = json.load(f)
d['plugins']['entries']['browser'] = {'enabled': False}
with open('/Users/mac/.openclaw/openclaw.json', 'w') as f:
    json.dump(d, f, indent=2)
# 然后重启 launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/ai.openclaw.gateway.plist
```

**对Jerry的意义**
这是 2026.4.25+ 版本 gateway 的已知问题。如果需要 OpenClaw 网页 UI 的浏览器自动化功能（browser 插件不能关），则需进一步排查 CDP 连接问题（如远程浏览器地址配置错误、chrome-headless 未启动等）。

**延伸思考**
- 2026.4.24 及之前版本的死锁原因不同（npm ENOTEMPTY 锁冲突，66个包安装耗时），两种情况的日志特征不同：旧版日志停在 "starting channels and sidecars..."，新版日志正常写入但 CDP 卡死
- 可用 `OPENCLAW_PROFILE=dev` 临时绕过去开发调试

**标签**：Hermes × OpenClaw × Gateway × CDP × 故障诊断
