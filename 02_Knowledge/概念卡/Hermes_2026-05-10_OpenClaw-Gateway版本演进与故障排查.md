# OpenClaw Gateway 版本演进与故障排查

**背景**
OpenClaw Gateway 是 Hermes 的核心承载层，负责各 channel（飞书、Telegram 等）的接入和插件运行。2026年4月24日至27日期间连续出现三次阻断性故障，每次根因不同，构成了一个完整的故障模式库。

**核心洞察**

## 版本演进时间线

| 日期 | 版本 | 核心问题 | 症状 |
|------|------|---------|------|
| 2026.4.24 及之前 | 旧版 | npm ENOTEMPTY 锁冲突导致插件安装 30 分钟+ | CLI 命令超时、0% CPU、日志停在 "starting..." |
| 2026.4.25–26 | 2026.4.25 | browser 插件 CDP 初始化卡死 gateway | 端口监听但不响应 HTTP、日志不写入 |
| 2026.4.27+ | 升级后 | 4 个版本 plugin-runtime-deps 互相引用缺失文件 + npm 网络不通一直重试 | 完全无响应，所有 CLI 命令卡死 |

## 三类核心症状模式

**模式一：假死（0% CPU，端口监听）**
- 进程存在，curl 不通，日志停写
- 根因：插件安装未完成（老版本）或 browser CDP 初始化卡死（新版本）
- 诊断：`kill -USR2 <pid>` 强制刷新日志缓冲区

**模式二：升级后彻底无法启动**
- 卸载+重装后进程存在但不监听端口
- 根因：launchd 管理混乱，旧进程未真正被杀掉
- 诊断：`pkill -9 -f "openclaw"` 强制杀进程后再 launchctl

**模式三：npm 锁冲突反复出现**
- 每次重启都重新安装 66 个插件依赖包
- 根因：gateway 每次启动都全量检查，ENOTEMPTY 时锁住
- 解法：`find ~/.openclaw/plugin-runtime-deps/ -name "*.lock" -delete` 清锁

## 对Jerry的意义

OpenClaw 是 Hermes 的生死线——gateway 挂了则所有 channel 均中断。每次升级必须留足回滚时间窗口（建议降级到 2026.4.25 方案先行）。**永远不要在线上环境直接升级 OpenClaw**。

**延伸思考**
- 飞书 channel probe 超时是启动延迟的主因（4 accounts × 30s = 2 分钟），关闭飞书 channel 可将启动时间从 10 分钟压缩到 3 分钟
- plugin-runtime-deps 多版本并存是升级大敌，建议在降级后立即删除多余版本目录：`rm -rf ~/.openclaw/plugin-runtime-deps/2026.4.27`
- 日志文件超过 600MB 会导致日志轮转异常，定期 truncate 是必要的预防性运维

**标签**：Hermes × OpenClaw × 运维 × 故障排查 × Gateway
