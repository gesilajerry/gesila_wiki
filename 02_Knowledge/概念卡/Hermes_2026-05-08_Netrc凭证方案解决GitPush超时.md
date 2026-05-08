# .netrc凭证方案解决Git Push超时

**背景**
OpenClaw/Hermes所在环境的网络到GitHub 443端口被代理拦截，导致常规Git认证方式（osxkeychain/gh auth/git-credential）全部失败。git push一直超时，osxkeychain/git-credential读取不到凭证。

**核心洞察**
- OpenClaw自己的Cron任务用gh auth方式push也超时，说明gh auth本身也依赖GitHub 443连接
- `gh auth token`能获取token，说明gh CLI有自己的HTTPS代理/证书配置，但git不知道这些配置
- `.netrc`文件是Git最早支持的凭证存储格式，优先级高于keychain，且可以用环境变量覆盖
- `GIT_TERMINAL_PROMPT=0`禁用git的交互式prompt，避免它在失败时跳窗
- `credential.helper=store`显式指定使用`.netrc`（store模式）

**对Jerry的意义**
在wiki平台ops和OpenClaw gateway的网络环境下，`.netrc+gh auth token`是Git push最稳定的方案：
```
machine github.com
login gesilajerry
password {gh auth token}
```
步骤：
1. `gh auth token` 获取当前token
2. 写入 `~/.netrc`，权限600
3. `GIT_TERMINAL_PROMPT=0 git -c credential.helper=store push origin main`

**延伸思考**
此方案比gh auth更底层——gh auth依赖GitHub CLI的认证状态，而.netrc直接是Git的协议级凭证，不依赖CLI。如果gh auth也失效（token过期/网络变更），可回退到Personal Access Token手动写入.netrc。建议定期（如每月）运行`gh auth status`检查token有效性，提前发现失效。

**标签**：Hermes × Git × 凭证管理 × 网络代理 × Wiki运维
