# ngrok Tunnel 端口配置混淆与自治诊断框架

**背景**
ngrok 在这个环境里同时为两个不同的本地服务提供公网访问：Wiki 平台（Flask 端口 5001）和 OpenClaw Gateway（端口 18789）。当两个 tunnel 的名称和端口配置不清晰时，会出现「URL 能通但内容不对」的奇怪问题——访问 wiki 的 ngrok URL，返回的却是 OpenClaw 的页面。

**核心洞察**
Wiki 平台运维手册中定义了两个 tunnel：
- `wiki` tunnel：proto=http，addr=5001 → Flask 维基平台
- `gateway` tunnel：proto=http，addr=18789 → OpenClaw Gateway

混淆症状：当 `gateway` tunnel 被错误启动时，访问 `https://unbribing-undeep-maximina.ngrok-free.dev`（本应是维基）实际指向 18789，看到的是 OpenClaw/Hermes 页面。URL 没变，但内容变了。

自治诊断三步法：
```bash
# Step 1: 确认进程在跑哪个 tunnel
ps aux | grep ngrok | grep -v grep

# Step 2: 确认 tunnel 实际指向的 addr
curl -s http://localhost:4040/api/tunnels | python3 -c "
import sys,json
[t print(t['name'], t['public_url'], '->', t['config']['addr']) 
  for t in json.load(sys.stdin).get('tunnels',[])]"

# Step 3: 若指向错误，杀掉重起正确的 tunnel
kill <ngrok_pid>
cd ~/Library/Application\ Support/ngrok && ./ngrok start wiki
```

ngrok API 还能动态管理 tunnel：
```bash
# 删除错误 tunnel
curl -X DELETE http://localhost:4040/api/tunnels/<name>

# 创建新 tunnel
curl -X POST http://localhost:4040/api/tunnels   -H 'Content-Type: application/json'   -d '{"proto":"http","addr":"5001"}'
```

**对Jerry的意义**
这类「服务能通但内容错」的问题非常隐蔽，容易被误判为代码问题或配置漂移。按照「进程 → tunnel 配置 → addr」的顺序排查，可以在30秒内定位根因，而不是反复检查应用层代码。

**延伸思考**
ngrok 多 tunnel 场景下的端口混淆，本质上是「一个公网入口对应多个内部服务」架构的常见问题。在更复杂的场景下，建议在 ngrok 配置中明确添加 subdomain 字段让每个 tunnel 有独立的子域名（如 `wiki.ngrok-free.dev` 和 `gateway.ngrok-free.dev`），从根本上避免歧义。

**标签**：Hermes × ngrok × DevOps × 故障排查