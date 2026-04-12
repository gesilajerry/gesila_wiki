# Ralph Watchdog 故障自动恢复系统

## 分类：案例库 > 技术系统

## 项目背景
habit_planet_ra Flutter项目开发，Ralph作为AI编程助手持续运行

---

## 问题现象

### 问题1：Circuit Breaker频繁跳闸
**症状：**
- Ralph运行约10-20分钟后circuit breaker触发
- Loop #3特定位置反复触发
- Token消耗每小时达300万+

**根因：**
- `.ralphrc`中`CB_NO_PROGRESS_THRESHOLD=3`过于敏感
- Claude Code执行15分钟超时导致误判

### 问题2：Permission Denied
**症状：**
- flutter/dart/wc等命令被ALLOWED_TOOLS阻止
- 导致session reset

**根因：**
- 权限白名单过严
- 部分Flutter开发命令未加入

---

## 解决方案

### 1. 调整熔断阈值
```bash
# 修改前
CB_NO_PROGRESS_THRESHOLD=3
CB_SAME_ERROR_THRESHOLD=5

# 修改后
CB_NO_PROGRESS_THRESHOLD=10
CB_SAME_ERROR_THRESHOLD=15
```

### 2. 扩展权限白名单
```bash
ALLOWED_TOOLS="...Bash(flutter *),Bash(dart *),Bash(wc *),Bash(cat *)..."
```

### 3. 建立Watchdog自动监控
- 每5分钟检查日志
- 超过11分钟无更新自动重启
- Circuit breaker reset后自动恢复

---

## 系统架构

```
Ralph进程
    ↓ 写入日志
.ralph/logs/ralph.log
    ↓ 每5分钟检查
Watchdog Cron
    ↓ 异常检测
自动重启脚本
    ↓
tmux session恢复
```

---

## 关键参数

| 参数 | 值 | 说明 |
|------|-----|------|
| MAX_CALLS_PER_HOUR | 300 | 每小时最大调用 |
| CLAUDE_TIMEOUT_MINUTES | 15 | 单次执行超时 |
| CB_NO_PROGRESS_THRESHOLD | 10 | 无进展阈值 |
| 检查间隔 | 5分钟 | Watchdog轮询 |
| 停止阈值 | 11分钟 | 无日志即重启 |

---

## 教训

1. **AI编程助手需要持续监控** — Claude Code长时间运行会有各种异常
2. **Circuit Breaker需要调参** — 默认值不一定适合所有场景
3. **权限白名单要充裕** — 开发环境比生产更宽松
4. **Watchdog是必需品** — 自动化恢复比人工干预更高效

---

## 应用场景
- Claude Code / Codex 长时间任务
- AI编程助手持续运行
- 需要7x24自动恢复的开发环境

---

*创建时间：2026-04-12*
*来源：habit_planet_ra项目Ralph故障排查*
