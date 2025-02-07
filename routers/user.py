from fastapi import APIRouter

router = APIRouter(
    prefix="/user",  # 공통 URL 경로 지정
    tags=["User"]  # API 그룹 태그
)

@router.post("/login")
async def user_login(id: str, pw: str):
    return {"id": id, "password": pw}

@router.post("/signup")
async def user_signup(
    id: str,
    pw: str,
    email: str,
    user_name: str
):
    return {
        "loginid": id,
        "password": pw,
        "email": email,
        "userName": user_name
    }

@router.get("/findPassword")
async def user_find_password(email: str):
    return {"email": email}

@router.get("/profile")
async def read_user_profile():
    return {"user_id": "the current user"}

@router.get("/{user_id}")
async def read_user(user_id: str):  # item_id → user_id로 변경
    return {"user_id": user_id}
