import os
from dotenv import load_dotenv
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext

load_dotenv()

# 비밀번호 해싱을 위한 CryptContext 객체 생성
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 비밀번호 해싱 함수
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# 비밀번호 확인 함수
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

SECRET_KEY = os.getenv("SECRET_KEY", "default_key")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))

# JWT 생성 함수
def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# JWT 토큰 검증 함수
def verify_token(token: str):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if datetime.utcnow() > datetime.utcfromtimestamp(payload.get("exp")):
            raise credentials_exception  # 만료된 토큰일 경우
        return payload  # payload는 토큰에서 디코딩된 사용자 정보
    except JWTError:
        raise credentials_exception

def get_current_user(token: str = Depends(oauth2_scheme)):
    return verify_token(token)
