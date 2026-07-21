---
title: macOS SMB 文件共享配置要点
date: 2026-07-21
tags: [macOS, SMB, 文件共享, 局域网, 网络配置]
---

## 概述

在 macOS 上通过 SMB 协议将文件夹共享给局域网内的 Windows 电脑访问，需要系统内置的文件共享功能配合 SMB 协议开启。

## 关键要点

### 1. sharing 命令路径
macOS 的 `sharing` 命令不在默认 `$PATH` 中，需要使用完整路径：
```bash
/usr/sbin/sharing -a "/目标文件夹路径"
```

### 2. 完整设置步骤
- **系统设置 → 通用 → 共享**：打开「文件共享」开关
- 点击右侧「选项…」，勾选「使用 SMB 来共享文件和文件夹」
- 在用户列表中勾选当前 macOS 用户
- 可选：通过终端 `sudo sharing -a "/path"` 添加共享点

### 3. 密码验证机制
Windows 访问 macOS SMB 共享时，使用 macOS 系统用户的登录账号和密码进行验证。如果 Mac 没有设置登录密码，需要先设置一个。

### 4. 从 Windows 连接
Windows 资源管理器地址栏输入：
```
\\192.168.x.x\share
```
（将 IP 替换为 Mac 的实际局域网 IP）

### 5. smbd 服务
可手动加载 SMB 守护进程：
```bash
sudo launchctl load -w /System/Library/LaunchDaemons/com.apple.smbd.plist
```

## 常见问题

- `sudo: sharing: command not found` → 需要使用 `/usr/sbin/sharing` 完整路径
- 连接不上 → 检查文件共享是否已开启、SMB 选项是否勾选、防火墙是否放行
- 提示密码错误 → 确保 Mac 用户有登录密码，Windows 输入的账号和密码正确
