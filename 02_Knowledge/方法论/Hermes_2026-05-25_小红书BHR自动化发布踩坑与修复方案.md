# 小红书BHR自动化发布踩坑与修复方案

**背景**
小红书梵高图文流水线（xhs_vangogh_gen.py）在cron自动执行时，图片生成和飞书发送均正常，但BHR（BrowserHub远程控制）自动发布反复失败，报错 `[bhr] 无法获取 WS URL`。该问题在2026-05-25的R1/R2/R4三批次中均出现，阻碍了全自动发布流程。

**核心洞察**
BHR模块依赖Chrome浏览器的WebSocket调试端口来获取WS URL，具体逻辑是通过读取 `/tmp/chrome_xhs.log` 文件获取日志中记录的WebSocket URL。问题出在日志文件未被写入。

根因分析：
1. **日志机制缺失**：Chrome浏览器实际在 `9543` 端口运行CDP（Chrome DevTools Protocol），但启动脚本未将WS URL写入约定路径 `/tmp/chrome_xhs.log`
2. **CDP端口已知**：既然Chrome在9543端口监听，就不需要依赖日志文件，直接查询CDP API即可获得WS URL
3. **快速修复思路**：`curl http://127.0.0.1:9543/json` 可以直接返回当前浏览器所有可用的WebSocket调试端点

修复方案（无需改Chrome启动方式）：
```python
# 替换 get_ws_url() 逻辑
import urllib.request, json
with urllib.request.urlopen('http://127.0.0.1:9543/json') as r:
    tabs = json.loads(r.read())
    ws_url = tabs[0]['webSocketDebuggerUrl']
```

**对Jerry的意义**
此问题是阻碍小红书梵高图文流水线实现"全自动无人值守"的最后一公里。图片生成+飞书发送已经可以cron自动跑，唯独小红书发布需要人工介入。修复后，每天10张插画的完整生产发布链路可以7×24h自动运转，大幅提升日产能。

**延伸思考**
1. **CDP端口稳定性**：Chrome浏览器9543端口是固定的，但不同浏览器实例可能抢占端口。下次遇到类似问题时，优先 `curl http://127.0.0.1:9543/json` 探测端口状态
2. **日志文件 vs API轮询**：日志文件依赖系统写入时序，CDP API是实时查询，后者更可靠
3. **BrowserHub替代方案**：如果CDP端口也不稳定，可以考虑用puppeteer-playwright的CDP端点直接控制，或者用小红书创作服务平台的API而非BrowserHub

**标签**：Hermes × 小红书 × BHR × CDP × 自动化
