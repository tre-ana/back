import os
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from routers import analysis, user
from routers.analysis import load_model
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import logging

# .env 파일에서 환경 변수 로드
load_dotenv()

# 환경 변수에서 중요한 정보 불러오기 (예: 데이터베이스 URL)
DATABASE_URL = os.getenv("DATABASE_URL")

# 데이터베이스 연결 설정 (SQLAlchemy)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="TreAna API",
    description="API for analyze trend services",
    version="1.0.0",
)

# 라우터 등록
app.include_router(user.router, prefix="/users", tags=["user-controller"])
app.include_router(analysis.router, prefix="/analysis", tags=["analysis-controller"])

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

