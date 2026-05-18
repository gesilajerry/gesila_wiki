# 小红书发布session过期问题与修复流程

**背景**
xhs_b_publish.py通过Puppeteer连接Chrome浏览器操控小红书网页端自动发布。2026-05-17的AI热点推送12:00任务失败，报错"session/cookie过期"。这是小红书自动化发布的常见阻塞问题。

**核心洞察**

## 问题特征

症状：xhs_b_publish.py返回FAIL，错误信息包含session/cookie相关描述
影响范围：所有依赖Chrome CDP会话的小红书发布任务
触发条件：小红书账号登录状态超过一定时间未活动，或token超过有效期

## 根因分析

小红书网页端登录状态由cookie维护，cookie存储在Chrome用户配置目录中（通常通过Puppeteer的user-data-dir指定）。当cookie过期或被小红书服务端 invalidated，Chrome中的登录状态失效，此时Puppeteer发送的请求会被重定向到登录页，导致发布API调用失败。

xhs-cli底层也使用Chrome CDP，遇到同样问题。

## 修复流程

**方案A（推荐）：QR码重新登录**

```bash
# 重新获取session/cookie
xhs-cli qr-login
# 按提示扫码登录，获取新的cookie
```

将新cookie配置到xhs_b_publish.py的cookie来源路径，或更新环境变量/配置文件。

**方案B：xhs-cli session刷新**

如果使用xhs-cli管理session，定期执行：
```bash
xhs-cli session refresh
```

**方案C：修复f-string语法错误（2026-05-17发现的bug）**

xhs_b_publish.py的另一个问题是：Python f-string中嵌入JS代码时，`{}`未转义为`{{}}`，导致语法错误。错误修复后的文件保存为`/tmp/xhs_b_publish_fixed.py`。

```python
# 错误写法：
script = f"const result = {js_code};"  # JS中的{}被Python f-string解析

# 正确写法：
script = f"const result = {js_code.replace('{', '{{').replace('}', '}}') if isinstance(js_code, str) else js_code};"
# 或更简单：JS代码片段不放在f-string中，先格式化再注入
```

## 预防措施

1. 设置cookie过期前自动刷新（通过cron定时任务定期刷新session）
2. 在cron任务失败告警中增加session有效性自检
3. 维护备用发布方案（如手动发布的降级流程）

**对Jerry的意义**
小红书自动化发布的session过期是导致日更流水线中断的常见原因。掌握快速重新登录的流程，可以将恢复时间从数小时压缩到10分钟以内。

**延伸思考**
所有依赖会话状态自动化的工具（小红书、微信、飞书等）都有session过期问题。可以建立统一的session健康管理机制：定期检测session有效性，临近过期前自动刷新，过期后自动触发重新认证。

**标签**：Hermes × 小红书 × xhs_b_publish × session过期 × 运维
