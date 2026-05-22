# Cron任务执行与日志归档流程

**背景**
Hermes Agent 的 cron 任务覆盖新闻推送（AI/财经/MLCC/半导体/原子级制造）、内容生成（xhs-vangogh）、平台运维（Wiki Git 双向同步）、知识沉淀（结构层提炼）四大类。每日归档量约20-23个任务输出文件。

**核心洞察**
1. **归档时机**：输入层归档在 22:30 执行（截取过去24小时窗口），结构层提炼在 23:00 执行——两者分离，避免单次任务过重。
2. **文件超大问题**：推送日报文件超大（~460KB+），原因是 Prompt 完整嵌入了调用的 SKILL.md 内容。实际 AI 生成的 Response 内容才是知识素材，用 emoji 标记（如 `"🤖 AI热点简报"`）来定位。
3. **GitHub secret scanning 拦截**：归档文件中若包含 GitHub Token，会被 GitHub 自动拦截。需要先将 token 全文替换为 `[GITHUB_TOKEN_REDACTED]` 后再 push。
4. **cron 执行结果不一定全成功**：AI热点推送 12:00 的 Koala博客成功但小红书失败（xhs_b_publish.py FAIL）、飞书发送失败（环境变量未设置）。归档时需如实记录失败项。

**对Jerry的意义**
- 日均 20+ cron 任务形成稳定的情报和内容管线
- 归档流程本身会产生超大文件，需要在结构层提炼时有意识跳过 Prompt，只提取 Response 内容
- GitHub 推送前检查文件内容，避免 secret scanning 拦截

**延伸思考**
- 飞书通知依赖环境变量 `$FEISHU_APP_ID` / `$FEISHU_APP_SECRET`，部分任务失败是因为环境变量未设置
- xhs_b_publish.py 的 session/cookie 过期是持续问题，需要定期刷新

**标签**：Hermes × Cron任务 × 日志归档流程
