from src.ingest import MultilingualTextSplitter

def test_japanese_tokenization():
    splitter = MultilingualTextSplitter(chunk_size=50, chunk_overlap=0)
    text = "私はAIアルゴリズム開発の面接に向けて準備しています。"
    chunks = splitter.split_text(text)
    
    # 日本語が形態素単位で処理され、結合されていることを確認
    assert len(chunks) > 0
    # 「私」や「面接」などの単語が含まれているか（破壊されていないか）の簡易チェック
    assert any("面接" in chunk for chunk in chunks)

def test_english_tokenization():
    splitter = MultilingualTextSplitter(chunk_size=20, chunk_overlap=0)
    text = "Hello world from Canada."
    chunks = splitter.split_text(text)
    
    # スペース区切りの言語が適切に処理されるか
    assert len(chunks) > 0
    assert "Hello world" in chunks[0] or "Hello" in chunks[0]
