[<img src="https://upload.wikimedia.org/wikipedia/commons/thumb/0/09/YouTube_full-color_icon_%282017%29.svg/40px-YouTube_full-color_icon_%282017%29.svg.png" width="24"> 查看视频](https://www.youtube.com/watch?v=isQ69wWhsxM)<br>
2025-05更新  
每6小时自动抓取的优选ip，形成ip.txt  
https://cf.vvhan.com/  https://ip.164746.xyz  
还有js自动生成的https://cf.090227.xyz 和 https://stock.hostmonit.com/CloudFlareYes

---

管理后台后端（文件式存储，无外部依赖）

本仓库新增了一个简单可用的管理后台后端，涵盖以下能力：
- 商品管理 CRUD：名称、描述（富文本 HTML 字符串）、价格（一次性/订阅）
- 订单与支付面板：筛选、状态修改、手动履约、退款/作废占位
- 资源：文件上传（Base64 方式）与码池（导入/分配/标记已用）
- 课程/章节管理：章节排序、富文本内容
- 公告/FAQ 管理：富文本内容
- 仪表盘视图接口：收入统计、订单数量、待审核/异常提醒（前端可直接接入 Recharts 渲染）

说明：该后端为标准库实现，避免引入额外依赖，便于在现有仓库中快速落地。前端管理台（如基于 shadcn/ui 的布局与权限守卫）可直接对接这些接口。

目录结构
- admin/core.py 核心 CRUD 与持久化（JSON 文件）
- admin/server.py 轻量 HTTP API（基于 http.server）
- admin/data/*.json 数据文件目录（自动生成）
- uploads/ 上传文件目录（自动创建）

启动
- 本地运行服务：
  python -m admin.server
  默认监听 http://127.0.0.1:8787

主要接口速览
- 商品
  - GET /admin/products 列表
  - POST /admin/products 创建
  - GET /admin/products/{id} 详情
  - PUT /admin/products/{id} 更新
  - DELETE /admin/products/{id} 删除（或 POST /admin/products/{id}/delete）
- 订单
  - GET /admin/orders?status=&start=&end= 筛选
  - POST /admin/orders 创建
  - POST /admin/orders/{id}/status 状态更新（pending/paid/fulfilled/refunded/voided）
  - POST /admin/orders/{id}/fulfill 手动履约（会自动分配码池可用码）
  - POST /admin/orders/{id}/refund 退款占位
  - POST /admin/orders/{id}/void 作废占位
- 资源
  - GET /admin/resources/files 列表
  - POST /admin/resources/files 上传（JSON：filename + content_base64 [+ content_type + metadata]）
  - GET /admin/code-pool?status= 可筛选码池
  - POST /admin/code-pool 批量导入 codes: string[]
- 课程/章节
  - GET /admin/courses / POST /admin/courses / PUT /admin/courses/{id} / DELETE /admin/courses/{id}
  - GET /admin/chapters?course_id= / POST /admin/chapters / PUT /admin/chapters/{id} / DELETE /admin/chapters/{id}
- 公告/FAQ
  - GET /admin/announcements?type=announcement|faq
  - POST /admin/announcements / PUT /admin/announcements/{id} / DELETE /admin/announcements/{id}
- 仪表盘
  - GET /admin/dashboard/metrics?days=30 返回 revenue_by_day / orders_by_day / pending_count / abnormal_count

数据导入/导出
- POST /admin/export 导出全量数据
- POST /admin/import 导入全量数据（注意覆盖）

前端接入建议
- 使用 Next.js + shadcn/ui 构建后台布局、导航与权限守卫
- Recharts 接入 /admin/dashboard/metrics 返回的时序数据直接绘制折线/柱状图
- 富文本字段直接存储 HTML 字符串，前端用安全容器渲染

安全注意
- 文件上传通过 Base64 写入 uploads/ 目录，服务端做了简单路径校验，生产环境请接入对象存储与鉴权。
