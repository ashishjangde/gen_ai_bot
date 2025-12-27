from fastapi import FastAPI
from app.router import api_router
from app.advices.global_exception_handler import GlobalExceptionHandler

app = FastAPI(
    debug=True,
    title="Chat LLM API",
    description="Chat LLM API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

GlobalExceptionHandler.register_exception_handlers(app)

app.include_router(api_router)

@app.get("/health" , include_in_schema=False)
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)