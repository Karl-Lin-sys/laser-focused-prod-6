# Multilingual RAG System (Canadian English, Japanese, Taiwanese Mandarin)

## 全体アーキテクチャ (Architecture Overview)
本システムは、限られた計算資源（メモリやCPU）の環境下でも効率的に動作するよう設計された軽量なRAG（検索増強生成）システムです。
ローカルリソースを圧迫しないため、LLMおよびEmbeddingモデルにはGoogleのGemini APIを利用し、ベクトルデータベースには軽量なChromaDBを採用しています。

### コンポーネント構成
1. **Document Ingestion (`src/ingest.py`)**: 
   - カナダ英語、日本語、台湾華語の特性に合わせたカスタムチャンキング（Janome/Jiebaを利用）を実行。
   - Gemini APIを用いてEmbeddingを生成し、ChromaDBに格納します。
2. **Retrieval & Generation (`src/app.py`)**: 
   - ユーザーのクエリをベクトル化し、ChromaDBから関連文書を検索。
   - 検索されたコンテキストとプロンプトをGemini (Google Generative AI) に渡し、回答を生成。
   - 軽量なWebフレームワーク（FastAPI）でAPIとして提供。
3. **Infrastructure**:
   - `Dockerfile`: マルチステージビルドを採用し、ランタイムのイメージサイズを最小化。古いノートPCでのビルド・起動の負担を軽減。
   - `docker-compose.yml`: 環境変数(`GOOGLE_API_KEY`)を安全に渡しつつ、コンテナを容易に起動。
   - `GitHub Actions`: Lint(flake8)およびテスト(pytest)を実行し、成功した場合のみDockerイメージをビルドするCIパイプライン。

## ディレクトリ構成 (Directory Structure)
```text
.
├── src/
│   ├── app.py             # 検索・回答生成（FastAPIアプリ）
│   └── ingest.py          # データ取り込み・カスタムチャンキング・ベクトル保存
├── tests/
│   └── test_tokenize.py   # トークナイズ処理の単体テスト
├── .github/
│   └── workflows/
│       └── main.yml       # CI/CDパイプライン (Lint -> Test -> Build)
├── Dockerfile             # マルチステージ最適化ビルド
├── docker-compose.yml     # コンテナオーケストレーション
├── requirements.txt       # 依存ライブラリ
└── README.md              # 本ドキュメント
```
