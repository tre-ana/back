from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from models import User
from database import SessionLocal
from sqlalchemy.exc import IntegrityError
from auth import create_access_token, verify_token, get_current_user  # auth.py에서 import

# 비밀번호 해싱을 위한 CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter()

# 의존성 주입: 데이터베이스 세션을 얻는 함수
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 비밀번호 해싱 함수
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# 비밀번호 확인 함수
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# 로그인: 아이디와 비밀번호로 사용자 인증
@router.post("/login")
async def user_login(id: str, pw: str, db: Session = Depends(get_db)):
    # 사용자 검색
    user = db.query(User).filter(User.email == id).first()
    
    if not user or not verify_password(pw, user.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    # JWT 토큰 발행
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

# 회원가입: 새로운 사용자 생성
@router.post("/signup")
async def user_signup(id: str, pw: str, email: str, user_name: str, db: Session = Depends(get_db)):
    # 이미 존재하는 이메일로 가입 시 오류 발생
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # 비밀번호 해싱 후 저장
    hashed_password = hash_password(pw)
    
    new_user = User(
        email=email,
        nickname=id,
        userName=user_name,
        password=hashed_password
    )
    
    try:
        db.add(new_user)
        db.commit()  # 변경사항 커밋
        db.refresh(new_user)  # 새로운 사용자 객체 업데이트
    except IntegrityError:
        db.rollback()  # 예외 발생 시 롤백
        raise HTTPException(status_code=400, detail="Error creating user")
    
    return {"message": "User created successfully", "userId": new_user.userId}

# 비밀번호 찾기: 이메일로 비밀번호 찾기 요청 처리
@router.get("/findPassword")
async def user_find_password(email: str, db: Session = Depends(get_db)):
    # 이메일로 사용자 찾기
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 이메일로 비밀번호 찾기 이메일을 보내는 로직 추가 가능
    # 예시로 단순히 사용자 정보를 반환
    return {"message": "Password reset instructions sent to your email", "email": email}

# 보호된 API 엔드포인트 예시: 로그인한 사용자만 접근 가능
@router.get("/protected")
async def protected_route(current_user: dict = Depends(get_current_user)):
    return {"message": "This is a protected route", "user": current_user}


# @router.get("/profile")
# async def read_user_profile():
#     return {"user_id": "the current user"}

# @router.get("/{user_id}")
# async def read_user(user_id: str):  # item_id → user_id로 변경
#     return {"user_id": user_id}
