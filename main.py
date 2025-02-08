from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from routers import analysis, search, user
from routers.analysis import load_model

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
def get_result(keyword: str):
    pos = 0
    neg = 0
    neu = 0
    
    res = search.search_naver(keyword)
    
    df = pd.DataFrame(js['items'])
    
    pd.set_option("display.max_columns", None)  # 모든 열 표시
    pd.set_option("display.max_rows", 100)  # 최대 100행까지 표시
    pd.set_option("display.width", 1000)  # 한 줄에 출력할 최대 글자 수
    pd.set_option("display.colheader_justify", "center")  # 컬럼명 가운데 정렬

    print(df[['description', 'postdate']])