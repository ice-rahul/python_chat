from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from anthropic import Anthropic
from dotenv import load_dotenv
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os
from promptEvaluator import PromptEvaluator

load_dotenv()

app = FastAPI()

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

class ChatRequest(BaseModel):
    messages: list[dict]

class TestCaseRequest(BaseModel):
    numTestCases: int
    prompt: str
    variables: list[str]

class EvaluateRequest(BaseModel):
    prompt: str
    testCasesJson: str
    additionalCriteria: str

@app.get("/")
def health_check():
    return {"status": "ok"}

def generate_streaming_response(message: list[dict]):
    with client.messages.stream(
        model="claude-haiku-4-5",
        messages=message,
        max_tokens=500,
    ) as stream:
        for text in stream.text_stream:
            yield text

@app.post("/chat")
@limiter.limit("5/minute")  
async def chat(request: Request, body: ChatRequest):
    try:
        return StreamingResponse(
            generate_streaming_response(body.messages),
            media_type="text/plain"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/evaluate")
async def evaluate(request: Request, body: EvaluateRequest):
    try:
        response = client.messages.create(
            model="claude-haiku-4-5",
            messages=body.messages,
            max_tokens=500,
        )
        return {"response": response["completion"]}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
      
@app.post("/generate-testcases")
async def generate_testcases(request: Request, body: TestCaseRequest):
    try:
        evaluator = PromptEvaluator(max_concurrent_tasks=1, api_key=request.headers.get('X-API-KEY'))
        dataset = evaluator.generate_dataset(
            task_description=body.prompt,
            prompt_inputs_spec=body.variables,
            output_file="dataset.json",
            num_cases=body.numTestCases,
        )

        return {"testcases": dataset}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
      