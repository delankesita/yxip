# 监控与告警（Sentry / 日志 / 告警渠道）

本方案覆盖前端/后端错误监控、运行日志收集，以及失败告警（邮件/钉钉/企业微信占位）。

## 1. Sentry 错误监控

- 新建 Sentry 项目（前端/后端各一）
- 生成 DSN，并在运行环境注入：`SENTRY_DSN`、`SENTRY_ENVIRONMENT`、`SENTRY_TRACES_SAMPLE_RATE`

### 1.1 Python（本仓库示例）

本仓库已在 `collect_ips.py` 中接入 Sentry（可选开启）：
- 在 CI 中安装 `sentry-sdk`（已处理）
- 在运行时设置 `SENTRY_DSN` 即可生效

环境变量（可选）：
- `SENTRY_TRACES_SAMPLE_RATE=0`（默认 0，若采样 APM 可设 0.1~1）
- `SENTRY_ENVIRONMENT=production`

### 1.2 Next.js（如你的 Web 项目）

- `@sentry/nextjs` 官方 SDK
- 关键环境变量：`SENTRY_AUTH_TOKEN`（仅在构建上传 SourceMap 时需要，保存于 CI Secret）
- 参考：https://docs.sentry.io/platforms/javascript/guides/nextjs/

## 2. 运行日志收集方案

- Vercel：可开启 Log Drains（导出到 DataDog、Better Stack、Logtail、Elastic 等）。
- GitHub Actions：默认保存 Job 日志，可结合失败告警（见下）或上传制品（Artifacts）。
- 自建：将应用日志输出到 stdout，使用 Log Agent（Vector/Fluent Bit）采集到对象存储或日志平台。

## 3. 告警通道（邮件 / 钉钉 / 企业微信）

本仓库新增了一个失败告警工作流 `.github/workflows/alerts.yml`：
- 触发条件：当工作流 “Update IP List” 运行失败时
- 动作：根据可用的 Secret 发送告警（任一渠道存在即可）

需要在仓库/组织 Secret 中配置（按需）：
- `RESEND_API_KEY`、`ALERT_EMAIL_FROM`、`ALERT_EMAIL_TO`
- `DINGTALK_WEBHOOK`（如需签名，可加 `DINGTALK_SECRET`）
- `WECOM_WEBHOOK`

注意：
- 所有 Secret 请配置在 GitHub Settings → Secrets → Actions。
- 发送模板位于工作流脚本中，可根据团队需要做细化。

## 4. SLO/阈值与升级路径

- 定时任务失败（单次）：告警（邮件 + 即时通信渠道）→ 观察
- 连续失败 ≥ 3 次或超过 24h 未成功：升级到值班人（电话/短信）
- 重要页面 JS 错误率 > 5% 持续 10 分钟：Sentry 触发 Issue + 通知

## 5. 仪表盘与报表（建议）

- Sentry：关键事务的错误率、吞吐量、P95/P99 响应时间
- 日志平台：任务成功/失败趋势、错误 TopN、异常模式聚类
- 每周自动导出周报到邮件（CI 定时 + 报表脚本）
