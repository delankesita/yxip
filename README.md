[<img src="https://upload.wikimedia.org/wikipedia/commons/thumb/0/09/YouTube_full-color_icon_%282017%29.svg/40px-YouTube_full-color_icon_%282017%29.svg.png" width="24"> 查看视频](https://www.youtube.com/watch?v=isQ69wWhsxM)<br>
2025-05更新  
每6小时自动抓取的优选ip，形成ip.txt  
https://cf.vvhan.com/  https://ip.164746.xyz  
还有js自动生成的https://cf.090227.xyz 和 https://stock.hostmonit.com/CloudFlareYes

---

开发与测试

- 依赖安装
  - python -m venv .venv && source .venv/bin/activate
  - pip install -r requirements.txt
- 运行脚本（默认写入 ip.txt，并在 audit.log 中记录审计日志）
  - python collect_ips.py
- 环境变量
  - CF_URLS: 逗号分隔自定义数据源列表（缺省使用脚本内置）
  - CF_AUDIT_LOG: 审计日志文件路径（缺省 audit.log）
- 单元测试与覆盖率
  - pytest
  - 生成覆盖率报告（xml）：pytest --cov --cov-report=xml

审计日志查看工具

- 通过脚本过滤查看关键操作是否被记录：
  - python scripts/audit_viewer.py --log audit.log --level INFO --grep fetch

CI 流水线

- .github/workflows/test.yml：在 Push/PR 上运行 pytest，生成覆盖率并上传为构建工件，作为防回归基线参考。
- .github/workflows/main.yml：每 6 小时运行一次采集脚本并自动提交 ip.txt 变更。

QA 清单

- 见 QA_CHECKLIST.md，包含关键功能验证步骤与发布前检查流程。
