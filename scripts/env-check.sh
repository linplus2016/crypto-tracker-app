#!/bin/bash
echo "=========================================="
echo "  服务器环境检查"
echo "=========================================="
echo ""

check_cmd() {
    if command -v $1 &> /dev/null; then
        echo "✓ $1 已安装: $($1 --version | head -1)"
    else
        echo "✗ $1 未安装"
    fi
}

echo "[Docker 环境]"
check_cmd docker
check_cmd docker-compose

echo ""
echo "[Git 环境]"
check_cmd git

echo ""
echo "[网络环境]"
echo "公网IP: $(curl -s ifconfig.me 2>/dev/null || echo '无法获取')"
echo ""

echo "[端口检查]"
if ss -tlnp | grep -q ':80 '; then
    echo "⚠ 端口 80 已被占用"
else
    echo "✓ 端口 80 可用"
fi

echo ""
echo "[磁盘空间]"
df -h / | tail -1

echo ""
echo "=========================================="
if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
    echo "  环境检查通过，可以部署!"
else
    echo "  请先安装 Docker 和 Docker Compose"
    echo "  Ubuntu/Debian: sudo apt install docker.io docker-compose"
    echo "  CentOS: sudo yum install docker docker-compose"
fi
echo "=========================================="
