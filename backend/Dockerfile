FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY app.py .
RUN mkdir -p cache

# 暴露端口
EXPOSE 5000

# 使用gunicorn运行
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "app:app"]
