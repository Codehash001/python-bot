from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import pandas as pd
from pandasai import Agent, SmartDataframe
from pandasai.llm import OpenAI
import time
from tenacity import retry, stop_after_attempt, wait_fixed
import os.path
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage,
)
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.readers.pandas_ai import PandasAIReader

app = FastAPI()

# Set up the LLM and DataFrame
llm = OpenAI(model_name="gpt-4o")


loader = PandasAIReader(pandas_llm=llm)

# Read the Excel file
df = pd.read_excel('data.xlsx')
sdf = SmartDataframe(df=df)

# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Set up LlamaIndex
PERSIST_DIR = "./storage"
if not os.path.exists(PERSIST_DIR):
    # load the documents and create the index
    documents = SimpleDirectoryReader("webdata").load_data()
    index = VectorStoreIndex.from_documents(documents)
    # store it for later
    index.storage_context.persist(persist_dir=PERSIST_DIR)
else:
    # load the existing index
    storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
    index = load_index_from_storage(storage_context)

# memory
memory = ChatMemoryBuffer.from_defaults(token_limit=1500)

# Create query engine
query_engine = index.as_chat_engine(
    system_prompt=(
        "You are a chatbot, able to have normal interactions, as well as talk. Answer in the same language that use to ask question."
        "You have to tell the details about the website 'https://lithyusmusic.com/' about how it works with the context provided."
        "Don't talk about terms and condition , always talk about basic usecase of the website that how user need to know about."
    ),
)


class Question(BaseModel):
    question: str

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/ask")
async def ask(question: Question):
    try:
        modified_question = f"{question.question} \n Give the answer in markdown list format. use the same language in the question.\n"
        response = loader.run_pandas_ai(
            df, modified_question, is_conversational_answer=True
        )
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@app.post("/web_query")
async def web_query(question: Question):
    try:
        response = query_engine.chat(question.question , memory)
        return {"response": str(response)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)