from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import portfolio

app = FastAPI(title="Portfolio Analytics API")

# Only the local React dev server may call the API from a browser, and only to read.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET"],
)

app.include_router(portfolio.router)


@app.get("/")
def root():
    return {"message": "Portfolio API is working"}
