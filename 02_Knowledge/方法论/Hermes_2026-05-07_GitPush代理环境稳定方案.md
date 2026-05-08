# Git Push在代理网络环境下的稳定推送方案

**背景**
OpenClaw/Hermes环境中，git push经常超时，osxkeychain和gh auth credential都无法读取GitHub token，网络到GitHub 443端口有代理拦截。

**核心洞察**

问题根源是：git credential helper（osxkeychain/gh auth git-credential）在代理环境下无法正确触发认证弹窗或读取钥匙串，导致Push一直卡在"waiting for username"阶段。

解决方案是绕过credential helper，直接用~/.netrc文件存储GitHub Personal Access Token：

```bash
# Step 1: 获取token
token=$(gh auth token)

# Step 2: 写入~/.netrc（权限必须600）
cat > ~/.netrc << EOF
machine github.com
login gesilajerry
password $token
EOF
chmod 600 ~/.netrc

# Step 3: Push（禁用terminal prompt + 指定store helper）
GIT_TERMINAL_PROMPT=0 git -c credential.helper=store push origin main
```

关键原理：
- ~/.netrc是git协议层面的fallback机制，不依赖任何credential helper
- credential.helper=store让git使用~/.netrc作为凭证源
- GIT_TERMINAL_PROMPT=0防止git在必要时弹出认证窗口（会卡住）

稳定性来源：HTTPS+PAT比SSH更稳定，因为大多数代理对443端口的HTTP协议处理更成熟，且PAT不依赖SSH密钥的端口转发。

**对Jerry的意义**

这个方案解决了wiki平台推送的最后一公里问题。每次结构层提炼完成后，用此方案推送，不再依赖OpenClaw自己的gh auth（OpenClaw cron任务中的gh auth方式也会Push超时）。属于一次配置、永久生效的运维经验。

**延伸思考**

如果token变更（如重新auth gh），需要重新生成~/.netrc。可以将Step 1-2做成cron任务的前置脚本，或设置定时任务每月更新一次netrc。

如果企业环境对HTTPS也做了SSL MITM检查，可能还需要关闭git的SSL验证：`git config --global http.sslVerify false`（谨慎使用）。

**标签**：Git运维 × 网络代理 × 开发效率 × 维基平台运维
