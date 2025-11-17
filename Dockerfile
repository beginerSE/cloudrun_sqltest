# ベースイメージ（軽めの python-slim）
FROM python:3.11-slim

# 必要な OS パッケージ（psycopg2 用）
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 作業ディレクトリ
WORKDIR /app

# 依存関係をコピーしてインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリ本体
COPY app.py .

# Cloud Run は PORT 環境変数を使う
ENV PORT=8080

# Gunicorn で起動
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]
