# GitHub Secrets 配置

在 GitHub 仓库 Settings → Secrets and variables → Actions 中添加以下 secrets：

## 必需 Secrets

| Secret Name | Value | 说明 |
|-------------|-------|------|
| `EC2_HOST` | `54.226.63.195` | EC2 实例 IP |
| `EC2_USER` | `admin` | SSH 用户 |
| `EC2_SSH_KEY` | `(SSH 私钥内容)` | sangwoo-key.pem 的内容 |

## 可选 Secrets

| Secret Name | Value | 说明 |
|-------------|-------|------|
| `API_BASE_URL` | `https://sangwoo.top/api` | 前端 API 地址 |

## 设置步骤

1. 打开 https://github.com/gamtsui/sangwoo.top/settings/secrets/actions
2. 点击 "New repository secret"
3. 添加上述 secrets
4. EC2_SSH_KEY 的值从 `C:/Users/GamTsui/sangwoo-key.pem` 复制全部内容

## 验证

配置完成后，推送代码到 main 分支将自动触发部署。

```bash
# 测试部署
git commit --allow-empty -m "ci: test deployment"
git push origin main
```

查看部署日志：https://github.com/gamtsui/sangwoo.top/actions
