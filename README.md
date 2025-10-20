[<img src="https://upload.wikimedia.org/wikipedia/commons/thumb/0/09/YouTube_full-color_icon_%282017%29.svg/40px-YouTube_full-color_icon_%282017%29.svg.png" width="24"> 查看视频](https://www.youtube.com/watch?v=isQ69wWhsxM)<br>
2025-05更新  
每6小时自动抓取的优选ip，形成ip.txt  
https://cf.vvhan.com/  https://ip.164746.xyz  
还有js自动生成的https://cf.090227.xyz 和 https://stock.hostmonit.com/CloudFlareYes

## 部署、监控与运维

本仓库附带一套可复用的部署与运维文档与工作流：

- 部署与域名（Vercel + HTTPS + DNS，示例域名：lanrenshu.us.kg）：docs/DEPLOY.md
- 监控与告警（Sentry / 日志收集 / 邮件 / 钉钉 / 企业微信）：docs/MONITORING.md
- 运维 Runbook（数据库备份、R2 生命周期策略、密钥管理、Cron/队列）：docs/RUNBOOK.md
- 环境变量模板：.env.example

CI 已配置：
- `.github/workflows/main.yml`：每 6 小时采集并更新 ip.txt；已可选上报 Sentry
- `.github/workflows/alerts.yml`：当“Update IP List”失败时触发告警（基于已配置的 Secrets）
- `.github/workflows/db_backup.yml`：每周自动备份数据库到 Cloudflare R2（Secrets 缺失时自动跳过）
