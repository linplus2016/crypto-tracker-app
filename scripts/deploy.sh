#!/bin/bash
set -e

echo "=========================================="
echo "  Crypto Tracker 部署脚本"
echo "=========================================="
echo ""

# 检查依赖
command -v docker >/dev/null 2>&1 || { echo "错误: Docker 未安装"; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "错误: Docker Compose 未安装"; exit 1; }

echo "[1/6] 环境检查..."
bash scripts/env-check.sh 2>/dev/null || true

echo ""
echo "[2/6] 拉取最新代码..."
if [ -d ".git" ]; then
    git pull origin main 2>/dev/null || echo "跳过 git pull"
fi

echo ""
echo "[3/6] 构建 Docker 镜像..."
docker-compose build --no-cache

echo ""
echo "[4/6] 启动服务..."
docker-compose up -d

echo ""
echo "[5/6] 等待服务启动..."
sleep 5

echo ""
echo "[6/6] 检查服务状态..."
docker-compose ps

echo ""
echo "=========================================="
echo "  部署完成!"
echo "=========================================="
echo ""
echo "访问地址:"
echo "  http://$(curl -s ifconfig.me 2>/dev/null || echo '你的服务器IP')"
echo ""
echo "API 测试:"
echo "  curl http://localhost/api/health"
echo "  curl http://localhost/api/price/btc"
echo ""
echo "常用命令:"
echo "  查看日志: docker-compose logs -f"
echo "  停止服务: docker-compose down"
echo "  重启服务: docker-compose restart"
echo "  更新代码: git pull && ./scripts/deploy.sh"
echo ""
