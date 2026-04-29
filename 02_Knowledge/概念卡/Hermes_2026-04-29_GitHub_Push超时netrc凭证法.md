# GitHub Push 超时 → netrc 凭证法

**背景**
在 Jerry 的网络环境中，到 GitHub 的 443 端口存在代理拦截，导致标准 `gh auth` 和 `git-credential-osxkeychain` 均无法读取凭证，`git push` 始终超时。OpenClaw 自身的 cron 任务用 `gh auth` 方式同样失败。

**核心洞察**
`~/.netrc` 文件比 osxkeychain/gh credential helper 更底层、更稳定：
- 网络代理环境下 osxkeychain/git-credential 的 HTTP 鉴权流程被干扰
- `.netrc` 凭证直接注入到 git 的认证层，绕过了 keychain 环节
- 配合 `GIT_TERMINAL_PROMPT=0` 和 `credential.helper=store` 双重保险

**操作步骤**
```bash
# 1. 获取 token
gh auth token
# → 输出类似 gho_xxxxxxxxxxxx

# 2. 创建 ~/.netrc（权限必须600）
cat > ~/.netrc << 'EOF'
machine github.com
login gesilajerry
password gho_xxxxxxxxxxxx
EOF
chmod 600 ~/.netrc

# 3. push
GIT_TERMINAL_PROMPT=0 git -c credential.helper=store push origin main
```

**对Jerry的意义**
所有 cron 任务中的 git push 统一用此方式，彻底解决 push 超时问题。尤其是 OpenClaw gateway 内部任务也无法用 gh auth，需改用 netrc。

**延伸思考**
- token 有效期与 gh auth token 相同，需定期刷新
- `.netrc` 凭证以明文存储，文件权限 600 是唯一保护，需注意机器物理安全
- 如果未来代理策略变化，可同时保留 netrc 和 gh auth 两种方式，git 会依次尝试

**标签**：Hermes × Git × 凭证 × 代理 × OpenClaw
