import logging
import os
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware
from routers import analysis, user, keyword, search
from pydantic import BaseModel
from dotenv import load_dotenv
from routers.analysis import load_model
from routers.search import search_naver, search_datalab
from routers.analysis import analyze_sentiment

from fastapi import Depends
from sqlalchemy.orm import Session
from database import get_db

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
import asyncio

load_dotenv()
load_model()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="TreAna API",
    description="API for analyze trend services",
    version="1.0.0",
)

scheduler = AsyncIOScheduler()

# CORS 미들웨어 설정
origins = [
    "http://127.0.0.1:8000",
    "http://localhost:5173",  # 클라이언트 개발환경
    os.getenv("FRONTEND_DOMAIN"),  # 배포된 프론트엔드 도메인
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 허용할 도메인
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)



# 라우터 등록
app.include_router(user.router, prefix="/users", tags=["user"])
app.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
app.include_router(keyword.router, prefix="/keywords", tags=["keywords"])
app.include_router(search.router, prefix="/search", tags=["search"])

# OpenAPI 스키마 수정
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Treana API",
        version="1.0.0",
        description="API documentation for Treana",
        routes=app.routes,
    )
    # BearerAuth 보안 설정
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    openapi_schema["security"] = [{"BearerAuth": []}]
    
    for path, methods in openapi_schema["paths"].items():
        for method, details in methods.items():
            if "parameters" in details:
                # Authorization 쿼리 파라미터 제거
                details["parameters"] = [
                    param for param in details["parameters"]
                    if param.get("name") != "authorization"
                ]
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

@app.post("/result")
async def get_result(keyword: str):
    # 정확도 기반 검색
    result = []
    data = search_naver(keyword)
    
    for desc, date in data:
        sentiment = analyze_sentiment(desc)
        result.append({"date": date, "description": desc, "sentiment": sentiment["predicted_class_label"]})
    
    return result


@app.post("/datalab")
async def get_datalab(body: dict):
    
    result = search_datalab(body)
    # 결과 반환
    return result


@app.get("/health")
def health_check():
    return {"status": "healthy"}


async def alert_auto_reports():    
    await keyword.generate_reports()


scheduler.add_job(alert_auto_reports, 'cron', hour=9, minute=0, timezone='Asia/Seoul')
scheduler.start()
