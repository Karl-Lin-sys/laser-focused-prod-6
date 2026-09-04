import os
import jieba
from janome.tokenizer import Tokenizer
from langchain.text_splitter import TextSplitter
from langchain.schema import Document
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

class MultilingualTextSplitter(TextSplitter):
    """
    カスタムチャンキング戦略: 
    英語などのスペース区切りの言語は標準的な分割を行いますが、日本語や台湾華語では
    意味を持つ最小単位（形態素・単語）が破壊されないよう、専用の形態素解析器を利用します。
    
    - 日本語: Janome (MeCabの代替として、システム依存がなく軽量・簡単に導入可能)
    - 台湾華語: Jieba (繁体字辞書の利用を推奨。ここでは標準のJiebaを利用して単語分割)
    
    設計意図: 
    標準のRecursiveCharacterTextSplitterでは指定文字数で強制的にカットされるため、
    「単語の途中」で分割され、Embeddingの品質や検索精度が著しく低下するリスクがあります。
    本クラスは、事前に文章を単語/形態素単位に分割し、それらをチャンクサイズに収まるように
    再結合することで、意味的な境界を保持したまま軽量にチャンク化を実現します。
    """
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50, **kwargs):
        super().__init__(chunk_size=chunk_size, chunk_overlap=chunk_overlap, **kwargs)
        self.janome_tokenizer = Tokenizer()
        
    def split_text(self, text: str) -> list[str]:
        # 言語の簡易判定（文字コード範囲等を利用）
        # 本番環境では langdetect 等を用いるか、メタデータから判断します。
        
        if any('\u3040' <= c <= '\u309f' or '\u30a0' <= c <= '\u30ff' for c in text):
            # 日本語（ひらがな・カタカナが含まれる場合）
            tokens = [token.surface for token in self.janome_tokenizer.tokenize(text)]
            separator = ""
        elif any('\u4e00' <= c <= '\u9fff' for c in text):
            # 台湾華語（漢字が含まれるが、かなが無い場合）
            # 台湾華語向けに jieba.set_dictionary('dict.txt.big') の利用が望ましいです
            tokens = list(jieba.cut(text, cut_all=False))
            separator = ""
        else:
            # カナダ英語・その他（スペース区切り）
            tokens = text.split(" ")
            separator = " "

        # トークンをチャンクにまとめる処理
        chunks = []
        current_chunk = []
        current_length = 0
        
        for token in tokens:
            token_len = len(token)
            if current_length + token_len > self._chunk_size and current_chunk:
                chunks.append(separator.join(current_chunk))
                # 簡易的なオーバーラップ処理 (最後の数トークンを残す)
                overlap_tokens = current_chunk[-max(1, len(current_chunk)//5):] if self._chunk_overlap > 0 else []
                current_chunk = overlap_tokens
                current_length = sum(len(t) for t in current_chunk) + (len(separator) * max(0, len(current_chunk)-1))
                
            current_chunk.append(token)
            current_length += token_len + (len(separator) if current_chunk else 0)
            
        if current_chunk:
            chunks.append(separator.join(current_chunk))
            
        return chunks

def ingest_data(documents: list[str], persist_directory: str = "./chroma_db"):
    """
    ドキュメントを取り込み、チャンク化してChromaDBに保存します。
    """
    # 1. カスタムスプリッターによるチャンク化
    splitter = MultilingualTextSplitter(chunk_size=500, chunk_overlap=50)
    docs = [Document(page_content=doc) for doc in documents]
    split_docs = splitter.split_documents(docs)
    
    # 2. Embeddingモデルの初期化 (Gemini APIを利用して計算をオフロード)
    # 認証には GOOGLE_API_KEY 環境変数が自動的に参照されます。
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    
    # 3. ChromaDBへ格納 (ローカル軽量ベクタDB)
    vectorstore = Chroma.from_documents(
        documents=split_docs, 
        embedding=embeddings, 
        persist_directory=persist_directory
    )
    vectorstore.persist()
    print(f"Data ingested successfully. Total chunks: {len(split_docs)}")

if __name__ == "__main__":
    # サンプルデータ
    sample_docs = [
        "In Canada, the maple leaf is a widely recognized national symbol.",
        "自然言語処理におけるRAGは、外部知識を検索して回答を生成する強力な手法です。",
        "在台灣，人工智慧與機器學習的發展正迅速改變科技產業的面貌。"
    ]
    ingest_data(sample_docs)
