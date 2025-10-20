# 部署与域名配置（Vercel + 自定义域）

本项目仓库以运维与监控为样例，提供一套可复用的部署与告警方案。尽管当前仓库主要用于定时采集与更新 IP 列表（GitHub Actions 已配置），但以下指南可用于在 Vercel 上部署 Web 项目，并与自定义域名绑定。

## 1. 规划与环境变量

将环境变量集中整理到 Vercel Project 的 Environment Variables 中，并在本仓库使用 `.env.example` 作为占位与约定。

关键变量（按需选择）：
- 数据库：`DATABASE_URL`（或 `POSTGRES_URL`）、`SUPABASE_URL`、`SUPABASE_ANON_KEY`
- Cloudflare R2：`R2_ACCOUNT_ID`、`R2_ACCESS_KEY_ID`、`R2_SECRET_ACCESS_KEY`、`R2_BUCKET`、`R2_ENDPOINT`
- 邮件发送（Resend）：`RESEND_API_KEY`、`ALERT_EMAIL_FROM`、`ALERT_EMAIL_TO`
- 监控（Sentry）：`SENTRY_DSN`、`SENTRY_ENVIRONMENT`、`SENTRY_TRACES_SAMPLE_RATE`
- 告警占位：`DINGTALK_WEBHOOK`、`WECOM_WEBHOOK`
- 认证（NextAuth，如需）：`NEXTAUTH_URL`、`NEXTAUTH_SECRET`、第三方 OAuth 的 Client/Secret

注意：所有生产机密只放在 Vercel/GitHub 的 Secrets 中，不要提交到仓库。

## 2. 在 Vercel 创建项目并接入 GitHub

1) 在 Vercel 新建 Project，选择 Import Git Repository，连接本仓库。
2) Framework 选择与你 Web 项目匹配的框架（例如 Next.js）。当前仓库不是前端项目，仅示范流程。
3) 在 Project Settings → Environment Variables 中一次性录入 `.env.example` 中列出的变量（按需）。
4) 打开 Production Branch（通常为 `main` 或 `release`），自动触发 CI/CD 部署。

## 3. 绑定自定义域名 lanrenshu.us.kg

1) 打开 Vercel → Project → Settings → Domains → Add → 输入 `lanrenshu.us.kg`。
2) 在域名 DNS 服务商处配置解析：
   - 根域名（apex）建议 A 记录指向：`76.76.21.21`
   - 子域名（如 `www`）添加 CNAME 记录到：`cname.vercel-dns.com`
3) 等待 DNS 生效（通常数分钟到 24h），Vercel 会自动签发 HTTPS 证书（Let's Encrypt）。
4) 在 Vercel 中将 `lanrenshu.us.kg` 设为 Primary Domain，必要时开启 Redirects（例如 `www` → 根域）。

## 4. 部署配置建议

- 分支策略：
  - `main`/`release`：生产环境
  - `dev`：预发环境
  - `feature/*`：开发分支，对应 Vercel Preview Deployments
- 审核保护：在 GitHub 打开分支保护（至少 1 人 Code Review，CI 通过才可合并）。
- 构建缓存/镜像：Vercel 默认处理，必要时在 `vercel.json` 中添加配置。

## 5. Cron/任务队列（Vercel 平台）

如需在 Vercel 部署定时任务，可用 `vercel.json` 配置 Serverless/Edge Functions 的 Crons，例如：

```
{
  "crons": [
    { "path": "/api/cron/daily", "schedule": "0 3 * * *" }
  ]
}
```

注意：当前仓库的定时任务由 GitHub Actions 执行（见 `.github/workflows/main.yml`）。如果迁移到 Vercel，请将逻辑封装为 HTTP API 并由 Vercel Cron 调用。

## 6. 回滚与排错

- 回滚：在 Vercel Deployments 列表中选择上一版本，Promote 为 Production。
- 排错：
  - 查看 Vercel Build/Runtime Logs
  - 前端错误：接入 Sentry 前端 SDK（见 Monitoring 文档）
  - 服务端错误：接入 Sentry 后端 SDK，或将日志导流到外部 Log 服务（DataDog/Better Stack 等）

