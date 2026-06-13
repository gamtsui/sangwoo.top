# 部署指南 — Vercel + Render（免费方案）

## 架构

```
用户 → sangwoo.top (DNS → Vercel)
   ├── 前端静态 → Vercel CDN（免费）
   └── API /api/* → 重写到 → Render 后端（免费）
```

## 步骤 1：部署后端到 Render

### 1.1 注册 Render 账号
- 访问 https://render.com
- 用 GitHub 账号登录

### 1.2 创建 Web Service
1. 点击 **New +** → **Web Service**
2. 连接 GitHub 仓库 `gamtsui/sangwoo.top`
3. 配置：
   - **Name**: `sangwoo-api`
   - **Root Directory**: `backend`
   - **Dockerfile**: 使用 `backend/Dockerfile`（自动检测）
   - **Free** 计划
4. **环境变量**（必须设置）：
   | Key | Value |
   |-----|-------|
   | `ADMIN_USERNAME` | 你的用户名 |
   | `ADMIN_PASSWORD` | 你的密码（强密码） |
   | `ADMIN_SECRET_KEY` | 随机生成（32字符） |
   | `DATABASE_URL` | `sqlite:////data/app.db` |
   | `FRONTEND_URL` | `https://sangwoo.top` |
5. **持久存储**（必须配置）：
   - **Disk**: `db-data`
   - **Mount Path**: `/data`
6. 点击 **Create Web Service**

### 1.3 记录 Render 分配的 URL
部署完成后，Render 会分配一个 URL，如：
```
https://sangwoo-api.onrender.com
```

记下这个 URL，后面要配置到 Vercel。

## 步骤 2：部署前端到 Vercel

### 2.1 注册 Vercel 账号
- 访问 https://vercel.com
- 用 GitHub 账号登录

### 2.2 导入项目
1. 点击 **Add New...** → **Project**
2. 连接 GitHub 仓库 `gamtsui/sangwoo.top`
3. 配置：
   - **Framework Preset**: Astro
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
4. 点击 **Deploy**

### 2.3 配置域名
1. 部署完成后，进入 **Settings** → **Domains**
2. 添加 `sangwoo.top` 和 `www.sangwoo.top`
3. Vercel 会给你 DNS 记录，到你的域名注册商处配置

### 2.4 配置 API 代理
在 Vercel **Settings** → **Functions** → **Rewrites** 中添加：
| Source | Destination |
|--------|-------------|
| `/api/:path*` | `https://sangwoo-api.onrender.com/api/:path*` |

（这个已经在 `vercel.json` 中配置了）

## 步骤 3：DNS 配置

在你的域名注册商（如 GoDaddy、Cloudflare）中设置：

| 类型 | 名称 | 值 | 说明 |
|------|------|-----|------|
| A | `sangwoo.top` | `76.76.21.21` | Vercel IP |
| CNAME | `www` | `cname.vercel-dns.com` | www 重定向 |

或直接用 Vercel 提供的 DNS 记录。

## 步骤 4：验证

### 4.1 测试后端
```bash
# 健康检查
curl https://sangwoo-api.onrender.com/health

# 获取产品列表
curl https://sangwoo-api.onrender.com/api/products
```

### 4.2 测试前端
```bash
# 访问首页
curl -I https://sangwoo.top/

# 应该 302 跳转到 /zh/
```

### 4.3 测试 API 代理
```bash
# 从前端访问 API（通过 Vercel 代理）
curl https://sangwoo.top/api/products
```

## 注意事项

### Render 免费版限制
- **每月 750 小时运行时间**（约 31 天，够用一个账号）
- **休眠机制**：空闲 15 分钟后休眠，首次唤醒可能需要 30-60 秒
- **解决方法**：用 UptimeRobot 免费监控保持活跃

### 环境变量
以下环境变量**不要**提交到 Git：
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`
- `ADMIN_SECRET_KEY`
- `DATABASE_URL`

在 Render 和 Vercel 的 Settings 中设置即可。

### 数据库迁移
从 EC2 迁移数据时：
1. 在 EC2 上备份数据库：`cp /data/app.db app.db.bak`
2. 上传到 Render：通过 Render CLI 或 SCP
3. 或在新环境运行种子数据：`python -m app.seed`

## 费用
- Vercel 前端：**$0/月**（免费计划）
- Render 后端：**$0/月**（免费计划）
- 域名：**$10/年**（已有）
- **总计：$0/月**
