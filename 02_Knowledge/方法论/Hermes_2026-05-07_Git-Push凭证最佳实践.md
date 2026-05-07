# Git Push凭证最佳实践

**背景**
Jerry的Hermes Cron任务频繁遇到 `git push` 超时，osxkeychain/gh credential 均无法读取到GitHub token——原因是网络到GitHub 443端口有代理拦截。

**核心洞察**
用 `~/.netrc` 文件存储GitHub token，比 `gh auth` 和 `git-credential` 更稳定可靠，是穿越代理的更优方案。

操作步骤：
1. 获取token：`gh auth token`
2. 创建 `~/.netrc`（权限600）：
```
machine github.com
login gesilajerry
password {token}
```
3. Push命令：
```bash
GIT_TERMINAL_PROMPT=0 git -c credential.helper=store push origin main
```

**对Jerry的意义**
- 解决了Cron任务中Git Push失败的历史问题
- 归档日志的commit现在可以稳定push
- 建议所有Cron任务的git操作统一使用此方式

**延伸思考**
- `credential.helper=store` 会读取 ~/.netrc，无需每次手动输入密码
- `GIT_TERMINAL_PROMPT=0` 禁止git弹出交互式认证提示，防止cron任务挂起
- 此方案已在OpenClaw cron任务中验证有效

**标签**：Hermes × Git × 凭证管理 × Cron任务