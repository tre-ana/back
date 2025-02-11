from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from models import User
from database import get_db
from sqlalchemy.exc import IntegrityError
from auth import create_access_token, get_current_user, verify_password, hash_password, is_valid_email
from pydantic import BaseModel

router = APIRouter()

class LoginRequest(BaseModel):
    email: str
    pw: str

# 로그인: 아이디와 비밀번호로 사용자 인증
@router.post("/login")
async def user_login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    
    if not user or not verify_password(request.pw, user.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    # JWT 토큰 생성
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


class SignupRequest(BaseModel):
    nickname: str
    pw: str
    email: str
    user_name: str

# 회원가입: 새로운 사용자 생성
@router.post("/signup")
async def user_signup(request: SignupRequest, db: Session = Depends(get_db)):
    # 이메일 형식 유효성 검사
    if not is_valid_email(request.email):
        raise HTTPException(status_code=400, detail="Invalid email format")    
    
    # 이미 존재하는 이메일로 가입 시 오류 발생
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # 비밀번호 해싱 후 저장
    hashed_password = hash_password(request.pw)
    
    new_user = User(
        nickname=request.nickname,
        userName=request.user_name,
        email=request.email,
        password=hashed_password
    )
    
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Error creating user")
    
    return {"message": "User created successfully", "userId": new_user.userId}

# 보호된 API 엔드포인트 예시: 로그인한 사용자만 접근 가능
@router.get("/protected")
async def protected_route(current_user: dict = Depends(get_current_user)):
    return {"message": "This is a protected route", "user": current_user}
