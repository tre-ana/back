from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from routers import analysis, search, user

from routers.search import search_naver
from routers.analysis import load_model, analyze_sentiment

import pandas as pd

# FastAPI 실행 시 모델 로드
try:
    load_model("model.pt")
except Exception as e:
    print(f"Error during model setup: {e}")

app = FastAPI(
    title="TreAna API",
    description="API for analyze trend services",
    version="1.0.0",
)

# 라우터 등록
app.include_router(user.router, prefix="/api", tags=["user-controller"])
app.include_router(analysis.router, prefix="/api", tags=["analysis-controller"])
app.include_router(search.router, prefix='/api', tags=["search-controller"])

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

@app.get("/")
async def get_result(keyword: str):
    pos = 0
    neg = 0
    neu = 0
    
    search = search_naver(keyword)
    
    for data in search:
        sentiment = analyze_sentiment(data)
        if sentiment["predicted_class_label"] == '긍정':
            pos += 1
        elif sentiment["predicted_class_label"] == '부정':
            neg += 1
        else:
            neu += 1
    
    return {
        '긍정': pos,
        '부정': neg,
        '중립': neu
    }