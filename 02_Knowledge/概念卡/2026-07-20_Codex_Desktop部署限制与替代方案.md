---
title: Codex Desktop 部署限制与替代方案
date: 2026-07-20
tags: [工具评估, AI编码, 本地部署, Codex]
source: daily-digest
---

# Codex Desktop 部署限制与替代方案

## 背景
尝试在 macOS 本地部署 OpenAI Codex Desktop 作为 AI 编码助手，发现了以下关键限制。

## 核心发现

### Codex Desktop 的限制
1. **强制 OpenAI 账号登录**：启动时必须登录 OpenAI 账号，无法绕过
2. **不支持自定义 API base URL**：无法接入第三方 API（如 DeepSeek、SynthSpace 等）
3. **需全球网络访问**：OpenAI 服务在国内受限时无法使用

### Codex CLI 的限制
- npm 全局安装后可运行，但同样强制要求 OpenAI 登录
- `--oss` 模式理论上可接本地 Ollama，但实际体验不佳

### 可行的替代方案
1. **OpenCode CLI**：原生支持自定义 OpenAI-compatible 后端
2. **Claude Code CLI**：支持自定义 API endpoint
3. **直接 Shell + API 调用**：无需中间层

## 操作记录
- 安装 `@openai/codex` npm 包成功
- 下载 Codex Desktop app（约200MB）
- 测试后发现登录限制无法绕过
- 用户决定删除：清除了 App、npm 包、配置目录和缓存
