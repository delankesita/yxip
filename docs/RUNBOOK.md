# 运维 Runbook（部署/监控/备份/任务）

本 Runbook 用于指导日常运维，包括部署流程、监控告警、数据库/对象存储策略，以及定时任务/队列的上线与排障。

---

## 1. 部署流程概览

- 代码合并策略：
  - `feature/*` → `dev` → `main`
  - 仅允许通过 PR 合并，确保 CI 通过 + Review 通过
- Vercel：
  - Preview：每个 PR 自动生成，验收后合入主分支
  - Production：`main` 或 `release` 分支自动部署
- 回滚：Vercel Deployments → Promote 上一版本

参考 docs/DEPLOY.md 获取更详细的 Vercel/DNS 配置说明。

---

## 2. 监控与告警

- Sentry：已在示例脚本接入，可扩展到前端/后端
- GitHub Actions 失败告警：见 `.github/workflows/alerts.yml`
- 日志平台：推荐使用 Vercel Log Drains 或第三方（DataDog/Better Stack/ELK）

遇到异常时：
1) 先看最近变更（部署、配置修改）
2) 查看平台日志与 Sentry 事件
3) 判定范围（前端/后端/网络/外部依赖）
4) 必要时回滚并开启告警静默窗口

---

## 3. 数据库策略（Neon / Supabase）

- 生产数据库建议使用：
  - Neon：提供分支/点时间恢复（PITR），注意存储与保留期配置
  - Supabase：自带每日自动备份，但仍建议自定义逻辑导出到对象存储
- 备份方案：
  - 周期性 `pg_dump` 导出 gzip 压缩文件
  - 加密（可选）：使用 KMS 或 GPG
  - 备份文件存储到 Cloudflare R2（低成本）
- 恢复演练：每季度选取备份文件做一次恢复演练，确保可用

本仓库已提供 DB 备份工作流样例 `.github/workflows/db_backup.yml`，当 Secrets 未配置时会自动跳过。

所需 Secrets：
- `POSTGRES_URL`（或 `DATABASE_URL`）
- `R2_ACCOUNT_ID`、`R2_ACCESS_KEY_ID`、`R2_SECRET_ACCESS_KEY`、`R2_BUCKET`

---

## 4. R2 生命周期与密钥管理

- 生命周期策略（R2 控制台 → Buckets → Lifecycle）：
  - `backups/` 前缀：保留最近 30 天的日备份、最近 12 周的周备份、最近 12 个月的月备份（按需）
  - 临时日志/中间文件：7 天自动清理
- 密钥管理：
  - 使用最小权限的 API Token，仅允许读/写指定 Bucket 与前缀
  - 将密钥存放于 Vercel/GitHub Secrets；半年轮换一次
  - 禁止将密钥写入仓库或容器镜像

---

## 5. 定时任务 / 队列

- GitHub Actions 定时任务：
  - 本仓库的 IP 列表采集脚本由 `.github/workflows/main.yml` 每 6 小时运行一次
  - 失败会触发 `.github/workflows/alerts.yml` 进行告警（前提：已配置 Secrets）
- Vercel Cron（如 Web 项目）：
  - 使用 `vercel.json` 的 `crons` 字段配置，触发 Serverless/Edge Functions
  - 避免长耗时任务（> 10 分钟），改用队列/独立 Worker
- 队列/消息总线：
  - 推荐使用 Cloudflare Queues、Supabase realtime、或托管 Redis（Upstash）
  - 关注重试、死信队列（DLQ）与幂等设计

日常任务示例：
- 订阅失效扫描：每日 03:00 扫描过期订阅并下发通知
- 审计归档：每周日 02:00 归档上周审计日志到 R2

---

## 6. 应急与演练

- 故障分级：P0（全站不可用）、P1（核心功能不可用）、P2（可降级）
- 半年一次全链路演练（含备份恢复、域名切换、告警通路）
- 事后复盘：明确根因、修复计划与预防措施，更新本 Runbook

---

## 7. 联系方式与值班

- 值班通讯录：见企业内部文档（或 PagerDuty/OnCall）
- 高优先级渠道：电话/SMS
- 常规渠道：邮件/IM 群（钉钉/企业微信/飞书）
