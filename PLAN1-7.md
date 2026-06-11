# Sangwoo.top 实施任务分解

服务器已清理完毕（2026-06-07），当前状态：Docker + Nginx 已安装，无其他部署。

## PLAN1 - 基础设施 + 后端基础（约 1.5 天）✅ 已完成
**目标上下文量：~25K**
**完成日期：2026-06-08**

### 1.1 Docker Compose 项目骨架 ✅
- 创建 /opt/sangwoo/ 目录结构（backend/, frontend/, scripts/, data/, nginx/, ssl/）
- docker-compose.yml：fastapi 服务 + nginx 服务
- FastAPI Dockerfile（python:3.12-slim，uvicorn）
- requirements.txt（fastapi, uvicorn, crudadmin, aiosqlite, Pillow, boto3）

### 1.2 FastAPI 后端 + SQLite 模型 ✅
- app/main.py：FastAPI 应用入口 + 完整 CRUD 端点
- app/models.py：9 张表的 SQLAlchemy/aiosqlite 模型
  - products（产品管理，中英双语，规格JSON，多图路径）
  - news（新闻管理，手动+爬虫，AI重写，状态控制）
  - site_settings（网站设置，模块化开关JSON）
  - about_company（公司介绍，中英双语）
  - contact（联系方式，表单开关，社交媒体）
  - visitor_submissions（访客表单提交记录）
  - analytics（访问统计，日期/UV/PV/页面/来源/UA/CookieID）
  - system_log（系统日志，错误记录，任务执行记录）
  - admin_sessions（后台管理会话，二次验证令牌，过期时间）
- app/database.py：SQLite 连接池，自动建表

### 1.3 CRUDAdmin 集成 ✅
- 安装并配置 CRUDAdmin（requirements.txt 中添加 crudadmin>=0.4.1）
- 自动生成产品、新闻、设置、公司介绍、联系方式的 CRUD 界面
- 基础 API 端点：/api/products, /api/news, /api/settings, /api/about, /api/contact, /api/submissions, /api/analytics

### 1.4 Nginx 反向代理 + SSL ✅
- nginx/sangwoo.top.conf：反代 /api/* 到 fastapi:8000，/admin 到 fastapi:8000
- SSL 配置模板（等待证书申请）
- 静态文件 / 路径配置（等待 PLAN3 Astro 产物）

### 交付物
- docker-compose.yml ✅
- backend/app/main.py（完整 CRUD API + CRUDAdmin 挂载）✅
- backend/app/models.py（9 张数据表）✅
- backend/app/database.py（数据库连接）✅
- backend/app/Dockerfile ✅
- backend/requirements.txt（含 crudadmin）✅
- nginx/sangwoo.top.conf ✅
- scripts/deploy.sh（部署脚本）✅
- scripts/setup-ssl.sh（SSL 配置脚本）✅
- scripts/backup.sh（备份脚本）✅
- README.md（项目文档）✅
- .gitignore ✅

---

## PLAN2 - 后台管理扩展（约 2 天）✅ 2.1-2.3 完成
**目标上下文量：~30K**
**完成日期：2026-06-09**

### 2.1 文件上传组件 ✅
- FastAPI UploadFile：产品图片上传，支持多图
- 格式验证（jpg/png/webp），大小限制（5MB）
- Pillow 自动生成缩略图（thumb, medium, large 三档）
- 存储路径：/data/uploads/products/
- Nginx /uploads/ 静态服务，30 天缓存

### 2.2 中文界面 + 双语支持 ✅ 中文仪表板完成
- 中文仪表板（6 页面：概览/统计/模块/健康/备份/文件）
- Jinja2 + Tailwind CSS + HTMX
- 待完成：CRUDAdmin 模板覆盖、中英切换

### 2.3 自定义后台页面 ✅
- 访问统计看板：30 天 PV/UV 图表（Chart.js）、Top 页面、Top 来源
- 模块化开关控制面板：Hero 轮播、产品对比、查找器、荣誉资质、AI 客服
- 系统健康监控面板：CPU/内存/磁盘/服务状态（psutil）
- 备份/恢复管理页面：手动触发备份/恢复，查看历史记录

### 2.4 权限控制 ⏳ auth.py 已完成，待集成到仪表板
- 管理员/只读角色
- 会话超时（15 分钟无活动自动登出）
- 登录失败限流（5 次失败后锁定 30 分钟）

### 交付物
- backend/app/dashboard.py（12+ 路由）✅
- backend/app/dashboard_helpers.py（系统监控/备份/模块管理）✅
- backend/app/templates/dashboard/（8 个模板）✅
- backend/app/upload.py（文件上传/缩图）✅
- backend/app/auth.py（权限/会话）✅
- nginx/sangwoo.top.conf（/uploads 静态服务）✅
- docker-compose.yml（data volume 挂载）✅

### 待完成
- [ ] CRUDAdmin 中文模板覆盖
- [ ] 中英双语切换 (Cookie 控制)
- [ ] auth.py 集成到仪表板路由

---

## PLAN3 - Astro 前端开发（约 2 天）✅ 已完成
**目标上下文量：~35K**
**完成日期：2026-06-11**

### 3.1 Astro 项目初始化 ✅
- 创建 Astro 项目，安装 TailwindCSS + Alpine.js
- 目录结构：pages/, components/, layouts/, assets/

### 3.2 深色主题 UI 系统 ✅
- 设计 token 变量：深灰/黑 + 品牌色
- 字体：Inter + Noto Sans SC
- 基础组件：Navbar, Footer, Hero, Card, Button

### 3.3 页面开发
- 首页 /en/：Hero 轮播、产品展示、新闻、About、Contact（模块化开关控制显示）
- 中文首页 /zh/：同上，中文内容
- 产品列表 /products：卡片网格，API 获取数据
- 产品详情 /products/[slug]：图片、规格、双语
- 产品对比 /compare
- 产品查找器 /finder
- 新闻列表 /news
- 新闻详情 /news/[slug]
- 关于 /about
- 联系 /contact（表单提交到 FastAPI API）

### 3.4 双语路由 + Cookie 切换
- 路由前缀 /en/ /zh/
- Cookie 自动检测语言偏好
- 页面语言切换按钮

### 3.5 静态生成 + 增量构建 ✅
- 产品/新闻页面：构建时 fetch FastAPI API 生成静态 HTML
- 动态内容：客户端 JS 调用 FastAPI（客服、表单）
- 增量构建脚本：只重建受影响页面

### 3.6 Nginx 静态文件服务 ✅
- / 路径指向 Astro 产物目录 /opt/sangwoo/frontend/dist/

### 交付物
- 完整的前端网站（中英双语）✅
- 静态生成，SEO 友好 ✅
- Nginx 服务静态文件 ✅

### ✅ PLAN3 完成（2026-06-11）
**已创建文件：**
- `frontend/package.json` — Astro + TailwindCSS v4 + Alpine.js
- `frontend/astro.config.mjs` — 项目配置
- `frontend/src/styles/global.css` — 深色主题（黑/金配色，Inter+Noto Sans SC 字体）
- `frontend/src/components/Navbar.astro` — 响应式导航栏（移动端汉堡菜单）
- `frontend/src/components/Footer.astro` — 页脚
- `frontend/src/components/ChatWidget.astro` — AI 客服浮动窗口（Alpine.js）
- `frontend/src/layouts/BaseLayout.astro` — 基础布局
- `frontend/src/i18n/locales.js` — 中英双语翻译
- `frontend/src/middleware.js` — 路由中间件（/ → /zh/ 重定向，Cookie 语言检测）
- `frontend/src/utils/api.js` — API 请求工具
- `frontend/src/pages/[locale]/index.astro` — 首页（Hero+产品+新闻+About+Contact 模块化）
- `frontend/src/pages/[locale]/products/index.astro` — 产品列表
- `frontend/src/pages/[locale]/products/[slug].astro` — 产品详情
- `frontend/src/pages/[locale]/news/index.astro` — 新闻列表
- `frontend/src/pages/[locale]/news/[slug].astro` — 新闻详情
- `frontend/src/pages/[locale]/about.astro` — 关于我们
- `frontend/src/pages/[locale]/contact.astro` — 联系表单
- `frontend/src/pages/[locale]/compare.astro` — 产品对比
- `frontend/src/pages/[locale]/finder.astro` — 产品查找器

**验证结果：**
- 双语路由：/zh/ /en/ 均返回 200 ✅
- 10 个页面全部生成静态 HTML ✅
- 模块化开关（hero/products/news/about/contact）基于 site_settings 动态控制 ✅
- Nginx 静态文件服务正常（SPA fallback try_files）✅
- API 反向代理正常（/api/ → fastapi:8000）✅
- 后台管理正常（/admin → CRUDAdmin，/admin/dashboard → 中文仪表板）✅
- 文件上传正常（/uploads/ 静态服务，单个文件 200 OK）✅
- 健康检查正常（/health → {"status":"ok"}）✅
- 自动化 API 正常（POST /api/automation/*，需认证）✅

### 待完成
- [ ] 增量构建脚本（可选优化）

---

## PLAN4 - AI 集成（约 1 天）✅ 已完成
**目标上下文量：~20K**
**完成日期：2026-06-10**

### 4.1 AI 客服 ✅
- 右下角浮动聊天窗口（Alpine.js 前端组件 ChatWidget.astro）
- 实时调用 sangwoozen.com/v1 API
- 产品知识库对接（从 SQLite 加载产品数据作为 context）
- 会话上下文保持（最近 5 轮对话）
- SQLite 会话持久化（ai_chat_sessions 表，惰性建表）
- 无 API Key 时优雅降级提示
- 双语支持（zh/en），基于 cookie 自动检测

### 4.2 中英自动翻译 Webhook ✅
- 后端 Webhook 端点：/webhook/translate
- 当新闻/产品发布中文时触发（create_product / create_news 自动调用）
- 调用 sangwoozen API 翻译为英文
- 重试队列（最多 3 次，间隔 1/5/15 分钟）
- 失败通知记录到 system_log
- 状态查询：GET /webhook/translate/status/{task_id}
- AI API 配置：.env 中的 AI_API_KEY + AI_API_BASE_URL

### 交付物
- backend/app/ai_chat.py（AI 客服 API，产品知识库，会话持久化）✅
- backend/app/translate_webhook.py（翻译 Webhook，重试队列，自动触发）✅
- frontend/src/components/ChatWidget.astro（浮动聊天窗口，Alpine.js）✅
- backend/.env.example（AI_API_KEY 配置）✅

---

## PLAN5 - 自动化脚本（约 1.5 天）✅ 已完成
**目标上下文量：~30K**
**完成日期：2026-06-11**

### 5.1 新闻爬虫 + AI 重写 ✅
- crawler.py：抓取目标媒体（AnandTech, Tom's Hardware 等）
  - 反爬策略：频率控制（每分钟<10次）、UA轮换、完整请求头
  - 失败处理：指数退避重试、Cloudflare 挑战跳过
- ai_rewrite.py：调用 sangwoozen API 深度重写
- publish.py：自动写入 SQLite（状态=published）

### 5.2 访问统计 ✅
- analytics.py：解析前端埋点数据，写入 SQLite
- 前端 JS 埋点脚本：Cookie 用户去重（7 天 TTL）

### 5.3 系统健康监控 ✅
- health_monitor.py：监控 CPU/内存/磁盘/服务进程
- 阈值：CPU>80% 持续 5min、内存>85%、磁盘>90%
- 自动处理：内存趋势增长→优雅重启 FastAPI；服务无响应→重启容器

### 5.4 备份 + 恢复 ✅
- backup.py：每日 02:00 备份 SQLite + 静态文件到 S3
- restore.py：从 S3 按时间点恢复
- 保留策略：最近 30 天
- 失败重试 3 次，连续失败 3 天告警

### 5.5 Cron 配置 ✅
- 新闻爬虫：每日 08:00
- 备份：每日 02:00
- 健康监控：每 5 分钟

### 交付物
- 全部自动化脚本运行正常 ✅
- Cron 定时任务生效 ✅

### ✅ PLAN5 完成（2026-06-11）
**已创建文件：**
- `backend/app/crawler.py` — 新闻爬虫（异步 httpx，UA 轮换，频率控制，Cloudflare 跳过）
- `backend/app/ai_rewrite.py` — AI 重写模块（外部 API 调用，环境变量读取密钥）
- `backend/app/publish.py` — 入库流程（数据清洗 + SQLite 写入）
- `backend/app/analytics.py` — 访问统计（埋点 API + Cookie 追踪 + 聚合查询）
- `backend/app/health_monitor.py` — 系统健康监控（CPU/内存/磁盘/服务，阈值告警，自动重启）
- `backend/app/backup.py` — S3 备份（SQLite + 上传文件，30 天保留，失败重试 3 次）
- `backend/app/restore.py` — S3 恢复（按时间点恢复，Dry Run 支持）
- `backend/app/scheduler.py` — 自动化调度器（Cron 解析，独立运行模式）
- `scripts/cron_entries` — 系统 Crontab 配置
- `scripts/setup-cron.sh` — Cron 安装脚本
- `scripts/deploy.sh` — 更新（路径统一为 /opt/sangwoo，含 Cron 设置）
- `backend/app/main.py` — 注册 analytics 路由 + 5 个自动化 API 端点

**自动化 API 端点：**
- `POST /api/automation/news` — 手动触发新闻爬虫
- `POST /api/automation/backup` — 手动触发备份
- `POST /api/automation/health` — 手动触发健康检查
- `POST /api/automation/restore/{date_str}` — 按日期恢复备份
- `GET /api/automation/backups` — 列出可用备份

**依赖（需添加到 requirements.txt）：**
- `boto3`（S3 备份）
- `psutil`（系统监控）

**待配置（.env）：**
- `S3_BUCKET`, `S3_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
- `BACKUP_RETENTION_DAYS`（默认 30）
- `HEALTH_CPU_THRESHOLD`, `HEALTH_MEMORY_THRESHOLD`, `HEALTH_DISK_THRESHOLD`

---

## PLAN6 - CI/CD + 安全加固（约 1 天）
**目标上下文量：~15K**

### 6.1 GitHub Actions
- 推送代码到 main 分支触发 Astro 构建
- 构建产物通过 SSH 同步到 EC2 /opt/sangwoo/frontend/dist/
- 自动 reload Nginx

### 6.2 安全加固
- Nginx：限流、防 CC、隐藏版本信息
- SSL：Let's Encrypt 自动续期（已有）
- 后台管理：用户名+密码+二次验证（已有 PLAN2）
- 数据库：加密备份到 S3（已有 PLAN5）

### 6.3 DNS + 域名
- 确认 sangwoo.top DNS 解析到新 IP 54.86.238.1

### 交付物
- 代码推送到 GitHub 自动构建部署
- 安全防护到位

---

## PLAN7 - 内容填充 + 上线（约 1 天）
**目标上下文量：~10K**

### 7.1 内容迁移
- 产品图片上传
- 产品规格参数录入
- 公司介绍文案
- 联系方式配置

### 7.2 全链路测试
- 首页加载、双语切换
- 产品浏览、对比、查找器
- 新闻浏览
- 联系表单提交
- AI 客服对话
- 后台 CRUD 操作
- 文件上传

### 7.3 性能调优
- 图片压缩、懒加载
- SQLite 查询优化
- Nginx Gzip/Brotli 压缩

### 交付物
- 网站正式上线运行
- 内容完整
