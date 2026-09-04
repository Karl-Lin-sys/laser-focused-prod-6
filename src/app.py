import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.chains import RetrievalQA

app = FastAPI(title="Multilingual RAG API", description="RAG system optimized for limited resources.")

# グローバル変数の初期化（起動時に一度だけロードし、メモリ消費を抑える）
vectorstore = None
qa_chain = None

def get_qa_chain():
    global vectorstore, qa_chain
    if qa_chain is None:
        persist_directory = "./chroma_db"
        if not os.path.exists(persist_directory):
            raise Exception("Vector database not found. Please run ingest.py first.")
            
        # EmbeddingとLLMはどちらもGemini APIを利用し、ローカルのCPU/RAMリソース消費を最小化
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        vectorstore = Chroma(persist_directory=persist_directory, embedding_function=embeddings)
        
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro-latest", temperature=0.3)
        
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vectorstore.as_retriever(search_kwargs={"k": 3})
        )
    return qa_chain

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    answer: str

@app.on_event("startup")
async def startup_event():
    # コンテナ起動時にチェーンを初期化
    try:
        get_qa_chain()
    except Exception as e:
        print(f"Startup warning: {e}")

@app.post("/ask", response_model=QueryResponse)
async def ask_question(request: QueryRequest):
    if not os.environ.get("GOOGLE_API_KEY"):
        raise HTTPException(status_code=500, detail="GOOGLE_API_KEY is not set.")
        
    try:
        chain = get_qa_chain()
        response = chain.run(request.query)
        return QueryResponse(answer=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # 軽量に動作させるためワーカー数は1に設定
    uvicorn.run(app, host="0.0.0.0", port=8000, workers=1)
