from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from routers import analysis, user
from routers.analysis import load_model

app = FastAPI(
    title="TreAna API",
    description="API for analyze trend services",
    version="1.0.0",
)

# 라우터 등록
app.include_router(user.router, prefix="/api", tags=["user-controller"])
app.include_router(analysis.router, prefix="/api", tags=["analysis-controller"])

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

