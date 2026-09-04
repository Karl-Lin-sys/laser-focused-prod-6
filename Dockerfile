# 1. Builder Stage: 依存関係のコンパイルと収集 (マルチステージビルドによる最適化)
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
# 古いノートPCでもビルドが遅くならないよう、バイナリパッケージを優先しつつ不要なキャッシュを削除
RUN pip install --no-cache-dir --user -r requirements.txt

# 2. Runtime Stage: 実行用軽量イメージ
FROM python:3.11-slim

WORKDIR /app
# ユーザーを作成し、ルート権限での実行を回避 (セキュリティベストプラクティス)
RUN useradd -m appuser

# builderステージからインストール済みのパッケージをコピー
COPY --from=builder /root/.local /home/appuser/.local
# ソースコードをコピー
COPY src/ /app/src/

# 環境変数の設定 (PATHを通す)
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONPATH=/app

# 権限の変更
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# 起動コマンド
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]
