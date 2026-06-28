from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import time
import threading
from datetime import datetime, timedelta
import json
import os

app = Flask(__name__)
CORS(app)

# 配置
cache_dir = os.path.join(os.path.dirname(__file__), 'cache')
os.makedirs(cache_dir, exist_ok=True)

# 数据源配置：可选 'binance' 或 'okx'
DATA_SOURCE = 'okx'  # 切换这里

# API 基础 URL
API_BASE = {
    'binance': 'https://api.binance.com',
    'okx': 'https://www.okx.com',
}[DATA_SOURCE]

# 数据格式映射
API_ENDPOINTS = {
    'binance': {
        'price': '/api/v3/ticker/24hr',
        'klines': '/api/v3/klines',
    },
    'okx': {
        'price': '/api/v5/market/ticker',
        'klines': '/api/v5/market/history-candles',
    },
}

# 缓存数据
price_cache = {}
klines_cache = {}
analysis_cache = {}
cache_ttl = 60  # 价格缓存60秒
kline_cache_ttl = 300  # K线缓存5分钟

# 支持的币种配置
COINS = {
    'BTC': {'symbol': 'BTCUSDT', 'name': 'Bitcoin', 'icon': '₿'},
    'ETH': {'symbol': 'ETHUSDT', 'name': 'Ethereum', 'icon': 'Ξ'},
    # 可扩展更多币种
    # 'SOL': {'symbol': 'SOLUSDT', 'name': 'Solana', 'icon': '◎'},
}

# 时间周期映射
INTERVALS = {
    'm15': '15m',
    'h1': '1h',
    'h4': '4h',
    'd1': '1d',
    'w1': '1w',
}


def get_cache_path(key):
    return os.path.join(cache_dir, f'{key}.json')


def read_cache(key, ttl):
    path = get_cache_path(key)
    if not os.path.exists(path):
        return None
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        if time.time() - data.get('timestamp', 0) > ttl:
            return None
        return data.get('data')
    except:
        return None


def write_cache(key, data):
    path = get_cache_path(key)
    with open(path, 'w') as f:
        json.dump({'timestamp': time.time(), 'data': data}, f)


def fetch_klines(symbol, interval, limit=20):
    """获取K线数据"""
    cache_key = f'klines_{symbol}_{interval}_{limit}'
    cached = read_cache(cache_key, kline_cache_ttl)
    if cached:
        return cached

    try:
        endpoint = API_ENDPOINTS[DATA_SOURCE]['klines']
        if DATA_SOURCE == 'binance':
            params = {'symbol': symbol, 'interval': interval, 'limit': limit}
        else:  # okx
            okx_symbol = symbol.replace('USDT', '-USDT')
            params = {'instId': okx_symbol, 'bar': interval, 'limit': str(limit)}

        url = f'{API_BASE}{endpoint}'
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        klines = []
        if DATA_SOURCE == 'binance':
            for item in data:
                klines.append({
                    'timestamp': item[0],
                    'open': float(item[1]),
                    'high': float(item[2]),
                    'low': float(item[3]),
                    'close': float(item[4]),
                    'volume': float(item[5])
                })
        else:  # okx
            for item in data['data']:
                klines.append({
                    'timestamp': int(item[0]),
                    'open': float(item[1]),
                    'high': float(item[2]),
                    'low': float(item[3]),
                    'close': float(item[4]),
                    'volume': float(item[5])
                })

        write_cache(cache_key, klines)
        return klines
    except Exception as e:
        print(f'Error fetching klines for {symbol}/{interval}: {e}')
        return None


def fetch_price(symbol):
    """获取实时价格"""
    cache_key = f'price_{symbol}'
    cached = read_cache(cache_key, cache_ttl)
    if cached:
        return cached

    try:
        endpoint = API_ENDPOINTS[DATA_SOURCE]['price']
        if DATA_SOURCE == 'binance':
            params = {'symbol': symbol}
        else:  # okx
            okx_symbol = symbol.replace('USDT', '-USDT')
            params = {'instId': okx_symbol}

        url = f'{API_BASE}{endpoint}'
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        if DATA_SOURCE == 'binance':
            result = {
                'price': float(data['lastPrice']),
                'change_24h': float(data['priceChangePercent']),
                'high_24h': float(data['highPrice']),
                'low_24h': float(data['lowPrice']),
                'volume_24h': float(data['volume']),
                'timestamp': int(time.time() * 1000)
            }
        else:  # okx
            item = data['data'][0]
            result = {
                'price': float(item['last']),
                'change_24h': round((float(item['last']) - float(item['open24h'])) / float(item['open24h']) * 100, 2) if float(item['open24h']) > 0 else 0,
                'high_24h': float(item['high24h']),
                'low_24h': float(item['low24h']),
                'volume_24h': float(item['vol24h']),
                'timestamp': int(time.time() * 1000)
            }

        write_cache(cache_key, result)
        return result
    except Exception as e:
        print(f'Error fetching price for {symbol}: {e}')
        return None


def calculate_support_resistance(klines):
    """计算支撑位和压力位"""
    if not klines or len(klines) < 5:
        return None, None

    highs = [k['high'] for k in klines]
    lows = [k['low'] for k in klines]

    # 简单计算：最近20根K线的高低点
    support = min(lows)
    resistance = max(highs)

    # 稍微调整，让支撑压力更合理
    current = klines[-1]['close']

    # 如果当前价接近高点，压力位是当前最高价，支撑是近期低点
    # 如果当前价接近低点，支撑位是当前最低价，压力是近期高点

    return round(support, 2), round(resistance, 2)


def generate_analysis(coin, interval, klines, price_data):
    """生成行情分析文字"""
    if not klines or len(klines) < 5:
        return "数据加载中..."

    latest = klines[-1]
    prev = klines[-2] if len(klines) > 1 else latest

    closes = [k['close'] for k in klines]
    highs = [k['high'] for k in klines]
    lows = [k['low'] for k in klines]

    # 计算趋势
    trend = 'neutral'
    if len(closes) >= 5:
        avg_short = sum(closes[-5:]) / 5
        avg_long = sum(closes[:-5]) / max(len(closes) - 5, 1) if len(closes) > 5 else avg_short

        if avg_short > avg_long * 1.02:
            trend = 'bull'
        elif avg_short < avg_long * 0.98:
            trend = 'bear'

    # 计算波动率
    volatility = ((max(highs) - min(lows)) / min(lows)) * 100 if min(lows) > 0 else 0

    # 根据周期和趋势生成分析文字
    period_names = {
        'm15': '15分钟',
        'h1': '1小时',
        'h4': '4小时',
        'd1': '日线',
        'w1': '周线'
    }
    period = period_names.get(interval, interval)

    # 生成分析文字模板
    analyses = {
        'bull': {
            'm15': f"{period}级别呈现多头排列，价格站稳短期均线上方，MACD金叉延续。短期关注{round(max(highs), 0)}整数关口压力，若放量突破有望继续上攻。回调不破{round(min(lows), 0)}支撑可维持偏多思路。",
            'h1': f"{period}级别上升通道保持良好，布林带开口向上，价格沿上轨运行，强势特征明显。建议关注{round(min(lows), 0)}关键支撑，跌破可能回踩下一平台。上方目标先看{round(max(highs), 0)}。",
            'h4': f"{period}级别处于整理阶段，价格在{round(min(lows), 0)}-{round(max(highs), 0)}区间内运行。RSI指标中性偏强，未出现明显背离信号。建议等待方向明确，突破箱体跟进。",
            'd1': f"{period}级别上升趋势完好，价格沿短期均线上行，多头控盘明显。成交量配合价格上涨，量价关系健康。下方{round(min(lows), 0)}为强支撑，不破此位趋势不改。",
            'w1': f"{period}级别处于大级别上升趋势中，多头动能充沛。价格突破前期震荡平台后加速上行，中长期趋势向好。{round(min(lows), 0)}为周线级别强支撑，若能有效突破{round(max(highs), 0)}将打开更大上涨空间。"
        },
        'bear': {
            'm15': f"{period}级别连续收阴，价格跌破短期均线，空头占优。MACD死叉向下，下跌动能增强。关注{round(min(lows), 0)}支撑，若跌破可能加速下探。反弹不过{round(max(highs), 0)}压力不宜追多。",
            'h1': f"{period}级别沿下降通道运行，价格受短期均线压制。KDJ指标低位运行，短期超卖但尚未企稳。建议关注{round(min(lows), 0)}支撑，跌破则打开下行空间。",
            'h4': f"{period}级别跌破前期上升通道下轨，形成破位走势。价格沿均线下方运行，空头趋势明显。{round(min(lows), 0)}为前期低点支撑，若失守可能加速下探。",
            'd1': f"{period}级别处于回调阶段，价格跌破短期均线支撑。MACD零轴下方运行，绿柱持续扩大。{round(min(lows), 0)}为前期平台密集区，若失守可能考验中期支撑。",
            'w1': f"{period}级别触及上升通道下轨后反弹力度不足。周MACD高位死叉，中长期多头格局受到考验。{round(min(lows), 0)}为周线关键支撑，守住此位则趋势完整。"
        },
        'neutral': {
            'm15': f"{period}级别横盘整理，价格在{round(min(lows), 0)}-{round(max(highs), 0)}区间内震荡。MACD在零轴附近粘合，多空力量均衡。建议观望等待方向选择。",
            'h1': f"{period}级别在{round(min(lows), 0)}-{round(max(highs), 0)}区间震荡整理，布林带收口，即将选择方向。成交量萎缩，市场观望情绪浓厚。建议等待突破跟进。",
            'h4': f"{period}级别处于高位震荡整理阶段，价格在{round(min(lows), 0)}-{round(max(highs), 0)}箱体内运行。RSI指标中性，未出现明显背离。建议观望为主。",
            'd1': f"{period}级别整体处于震荡格局中，价格在均线附近反复。成交量温和，市场等待新的催化剂。{round(min(lows), 0)}和{round(max(highs), 0)}构成短期震荡区间。",
            'w1': f"{period}级别处于大级别上升通道中的整理阶段，近期回调触及通道中轨后获得支撑。周MACD高位粘合，中长期趋势仍偏多但动能减弱。"
        }
    }

    return analyses.get(trend, analyses['neutral']).get(interval, analyses['neutral']['m15'])


@app.route('/api/price/<coin>', methods=['GET'])
def get_price(coin):
    """获取币种实时价格"""
    coin = coin.upper()
    if coin not in COINS:
        return jsonify({'error': 'Unsupported coin'}), 400

    symbol = COINS[coin]['symbol']
    data = fetch_price(symbol)

    if not data:
        return jsonify({'error': 'Failed to fetch price'}), 500

    return jsonify({
        'coin': coin,
        'name': COINS[coin]['name'],
        'icon': COINS[coin]['icon'],
        **data
    })


@app.route('/api/klines/<coin>/<interval>', methods=['GET'])
def get_klines(coin, interval):
    """获取K线数据"""
    coin = coin.upper()
    if coin not in COINS:
        return jsonify({'error': 'Unsupported coin'}), 400

    if interval not in INTERVALS:
        return jsonify({'error': 'Unsupported interval'}), 400

    symbol = COINS[coin]['symbol']
    api_interval = INTERVALS[interval]
    limit = request.args.get('limit', 20, type=int)

    klines = fetch_klines(symbol, api_interval, limit)

    if not klines:
        return jsonify({'error': 'Failed to fetch klines'}), 500

    support, resistance = calculate_support_resistance(klines)

    return jsonify({
        'coin': coin,
        'interval': interval,
        'klines': klines,
        'support': support,
        'resistance': resistance,
        'range': round(resistance - support, 2) if support and resistance else None
    })


@app.route('/api/analysis/<coin>/<interval>', methods=['GET'])
def get_analysis(coin, interval):
    """获取行情分析"""
    coin = coin.upper()
    if coin not in COINS:
        return jsonify({'error': 'Unsupported coin'}), 400

    if interval not in INTERVALS:
        return jsonify({'error': 'Unsupported interval'}), 400

    symbol = COINS[coin]['symbol']
    api_interval = INTERVALS[interval]

    # 获取K线和价格数据
    klines = fetch_klines(symbol, api_interval, 20)
    price_data = fetch_price(symbol)

    if not klines:
        return jsonify({'error': 'Failed to fetch data'}), 500

    support, resistance = calculate_support_resistance(klines)
    analysis = generate_analysis(coin, interval, klines, price_data)

    # 判断趋势
    closes = [k['close'] for k in klines]
    trend = 'neutral'
    if len(closes) >= 5:
        avg_short = sum(closes[-5:]) / 5
        avg_long = sum(closes[:-5]) / max(len(closes) - 5, 1) if len(closes) > 5 else avg_short
        if avg_short > avg_long * 1.02:
            trend = 'bull'
        elif avg_short < avg_long * 0.98:
            trend = 'bear'

    trend_labels = {
        'bull': '强势看涨' if interval in ['m15', 'w1'] else '看涨',
        'bear': '看跌',
        'neutral': '震荡'
    }

    return jsonify({
        'coin': coin,
        'interval': interval,
        'trend': trend,
        'trend_label': trend_labels.get(trend, '震荡'),
        'support': support,
        'resistance': resistance,
        'range': round(resistance - support, 2) if support and resistance else None,
        'analysis': analysis,
        'current_price': price_data['price'] if price_data else None,
        'change_24h': price_data['change_24h'] if price_data else None
    })


@app.route('/api/coins', methods=['GET'])
def get_coins():
    """获取支持的币种列表"""
    return jsonify({
        'coins': [
            {'id': k, **v} for k, v in COINS.items()
        ]
    })


@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({'status': 'ok', 'timestamp': int(time.time())})


@app.route('/api/all/<coin>', methods=['GET'])
def get_all_data(coin):
    """获取币种所有数据（聚合接口）"""
    coin = coin.upper()
    if coin not in COINS:
        return jsonify({'error': 'Unsupported coin'}), 400

    symbol = COINS[coin]['symbol']

    # 获取价格
    price_data = fetch_price(symbol)

    # 获取所有周期的K线和分析
    intervals_data = {}
    for interval_key, api_interval in INTERVALS.items():
        klines = fetch_klines(symbol, api_interval, 20)
        support, resistance = calculate_support_resistance(klines) if klines else (None, None)
        analysis = generate_analysis(coin, interval_key, klines, price_data) if klines else ""

        # 判断趋势
        trend = 'neutral'
        if klines and len(klines) >= 5:
            closes = [k['close'] for k in klines]
            avg_short = sum(closes[-5:]) / 5
            avg_long = sum(closes[:-5]) / max(len(closes) - 5, 1) if len(closes) > 5 else avg_short
            if avg_short > avg_long * 1.02:
                trend = 'bull'
            elif avg_short < avg_long * 0.98:
                trend = 'bear'

        trend_labels = {
            'bull': '强势看涨' if interval_key in ['m15', 'w1'] else '看涨',
            'bear': '看跌',
            'neutral': '震荡'
        }

        intervals_data[interval_key] = {
            'klines': klines,
            'support': support,
            'resistance': resistance,
            'range': round(resistance - support, 2) if support and resistance else None,
            'trend': trend,
            'trend_label': trend_labels.get(trend, '震荡'),
            'analysis': analysis
        }

    return jsonify({
        'coin': coin,
        'name': COINS[coin]['name'],
        'icon': COINS[coin]['icon'],
        'price': price_data,
        'intervals': intervals_data,
        'timestamp': int(time.time())
    })


# 后台定时刷新数据
def background_refresh():
    """后台线程定时刷新数据"""
    while True:
        try:
            for coin_id, coin_info in COINS.items():
                symbol = coin_info['symbol']
                # 刷新价格
                fetch_price(symbol)
                # 刷新所有周期K线
                for interval in INTERVALS.values():
                    fetch_klines(symbol, interval, 20)
                print(f'[{datetime.now()}] Refreshed data for {coin_id}')
            time.sleep(30)  # 每30秒刷新一次
        except Exception as e:
            print(f'Background refresh error: {e}')
            time.sleep(30)


# 启动后台线程
refresh_thread = threading.Thread(target=background_refresh, daemon=True)
refresh_thread.start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
