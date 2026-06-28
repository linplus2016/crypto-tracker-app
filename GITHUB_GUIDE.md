# GitHub 上传指南

## 步骤 1: 在 GitHub 创建仓库

1. 访问 https://github.com/new
2. 输入仓库名称: `crypto-tracker-app`
3. 选择 "Public" 或 "Private"
4. 点击 "Create repository"

## 步骤 2: 本地初始化并推送

```bash
# 进入项目目录
cd crypto-tracker-app

# 初始化 git
git init

# 添加所有文件
git add .

# 提交
git commit -m "Initial commit: Crypto Tracker fullstack app"

# 关联远程仓库（替换为你的用户名）
git remote add origin https://github.com/你的用户名/crypto-tracker-app.git

# 推送到 GitHub
git branch -M main
git push -u origin main
```

## 步骤 3: 服务器部署

```bash
# 在服务器上 clone 代码
git clone https://github.com/你的用户名/crypto-tracker-app.git
cd crypto-tracker-app

# 一键部署
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

## 步骤 4: 配置域名（可选）

如果使用域名，修改 `nginx/nginx.conf`:

```nginx
server {
    listen 80;
    server_name yourdomain.com;  # 修改为你的域名

    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://backend:5000/api/;
        # ...
    }
}
```

## 步骤 5: 配置 HTTPS（推荐）

使用 Let's Encrypt 免费证书:

```bash
# 安装 certbot
docker run -it --rm   -v "$(pwd)/certbot:/etc/letsencrypt"   -v "$(pwd)/certbot/www:/var/www/certbot"   certbot/certbot certonly   --webroot -w /var/www/certbot   -d yourdomain.com

# 修改 docker-compose.yml 挂载证书
# 修改 nginx.conf 配置 SSL
```

## 更新代码

```bash
# 本地修改后
git add .
git commit -m "Update: xxx"
git push origin main

# 服务器上更新
cd crypto-tracker-app
git pull origin main
./scripts/deploy.sh
```
