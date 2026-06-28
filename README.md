# Crypto Tracker - 加密行情追踪

一个基于 Binance API 的实时加密货币行情追踪应用，支持 BTC、ETH 等主流币种的多周期趋势分析。

## 功能特性

- 实时价格展示（来自 Binance API）
- 多周期 K 线图表（15分钟 / 1小时 / 4小时 / 1天 / 1周）
- 自动计算支撑位和压力位
- AI 智能行情分析（140字以内）
- 深浅色主题切换
- 响应式设计，支持移动端
- 自动定时刷新数据

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | HTML5 + Tailwind CSS + Canvas |
| 后端 | Python Flask + Gunicorn |
| 数据源 | Binance API (免费，无需 API Key) |
| 部署 | Docker + Docker Compose + Nginx |

## 快速开始

### 方式一：Docker 部署（推荐）

```bash
# 1. 克隆代码
git clone https://github.com/yourusername/crypto-tracker-app.git
cd crypto-tracker-app

# 2. 一键部署
chmod +x scripts/deploy.sh
./scripts/deploy.sh

# 3. 访问 http://你的服务器IP
```

### 方式二：手动部署

```bash
# 后端
cd backend
pip install -r requirements.txt
python app.py

# 前端（另开终端）
cd frontend
python -m http.server 8080

# 访问 http://localhost:8080
```

## 项目结构

```
crypto-tracker-app/
├── backend/
│   ├── app.py              # Flask 主应用
│   ├── requirements.txt    # Python 依赖
│   └── Dockerfile          # 后端镜像
├── frontend/
│   ├── index.html          # 前端页面
│   └── Dockerfile          # 前端镜像
├── nginx/
│   └── nginx.conf          # Nginx 配置
├── scripts/
│   └── deploy.sh           # 一键部署脚本
└── docker-compose.yml      # Docker Compose 配置
```

## API 接口

| 接口 | 说明 | 示例 |
|------|------|------|
| `GET /api/price/{coin}` | 实时价格 | `/api/price/btc` |
| `GET /api/klines/{coin}/{interval}` | K线数据 | `/api/klines/btc/h1` |
| `GET /api/analysis/{coin}/{interval}` | 行情分析 | `/api/analysis/btc/d1` |
| `GET /api/all/{coin}` | 聚合数据 | `/api/all/btc` |
| `GET /api/coins` | 币种列表 | `/api/coins` |
| `GET /api/health` | 健康检查 | `/api/health` |

## 扩展更多币种

在 `backend/app.py` 中修改 `COINS` 配置：

```python
COINS = {
    'BTC': {'symbol': 'BTCUSDT', 'name': 'Bitcoin', 'icon': '₿'},
    'ETH': {'symbol': 'ETHUSDT', 'name': 'Ethereum', 'icon': 'Ξ'},
    'SOL': {'symbol': 'SOLUSDT', 'name': 'Solana', 'icon': '◎'},
    'XRP': {'symbol': 'XRPUSDT', 'name': 'Ripple', 'icon': '✕'},
}
```

## 配置说明

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| `CACHE_TTL` | 60 | 价格缓存时间（秒） |
| `KLINE_CACHE_TTL` | 300 | K线缓存时间（秒） |

## 常见问题

**Q: 数据更新频率？**
A: 后端每30秒自动刷新，前端每5分钟自动刷新，也可手动点击刷新按钮。

**Q: 需要 API Key 吗？**
A: 不需要，使用 Binance 公共 API，完全免费。

**Q: 支持 HTTPS 吗？**
A: 建议配合 Nginx 或 Cloudflare 配置 SSL 证书。

## License

MIT
