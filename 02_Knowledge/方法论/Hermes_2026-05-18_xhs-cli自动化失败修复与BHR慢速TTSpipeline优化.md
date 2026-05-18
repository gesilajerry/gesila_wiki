# xhs-cli自动化失败修复与BHR慢速TTS pipeline优化

**背景**
2026年5月18日，多个xhs-vangogh cron任务（r1、r2、r4、r5）出现同一问题：BHR自动发布失败，错误信息为 `Cannot find module '/Users/mac/.npm-global/lib/node_modules/xhs-cli/node_modules/puppeteer-core'`。图片已生成完毕，但小红书自动发布环节全面失败。

**核心洞察**

**问题根因**：`xhs-cli` 依赖的 `puppeteer-core` 模块缺失，可能是 npm 全局包损坏或路径问题。

**修复命令**：
```bash
cd ~/.npm-global/lib/node_modules/xhs-cli
npm install puppeteer-core
# 或强制重装
npm install -g xhs-cli --prefix /Users/mac/.npm-global --force
```

**另一个报错变体**（原子级制造、半导体晨报任务中出现）：
- 错误：`uploadBtn.click is not a function`
- 这是在小红书网页表单填写时，上传按钮的 DOM 操作失败
- 原因：xhs-cli 使用的是老版本 DOM 选择器，新版小红书页面可能已变更 DOM 结构

**对Jerry的意义**
- xhs-vangogh pipeline 的图片生成和飞书发送是正常的，阻塞点在BHR小红书自动发布
- 这个失败是系统性的（所有xhs任务同时失败），不是偶发的
- 建议：将图片生成路径（`/tmp/xhs_vangogh/r40*/`）记录下来，方便手动发布时快速定位

**延伸思考**
xhs-cli 的浏览器自动化依赖 puppeteer-core，本质上是在 Node.js 环境中模拟 Chrome 操作。小红书网页经常改版，DOM 选择器容易失效。建议：
1. 定期测试 xhs-cli 的 publish 功能，及早发现 DOM 结构变更
2. 考虑用小红书官方创作服务平台 API 替代浏览器自动化，绕过 DOM 依赖
3. 建立失败监控——当 xhs-vangogh 任务连续失败超过3次，自动告警

**标签**：Hermes × xhs-cli × 自动化 × BHR × 浏览器控制
