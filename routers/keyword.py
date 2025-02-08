from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Keyword, Favorite
from auth import get_current_user
from pydantic import BaseModel

router = APIRouter()

class KeywordRequest(BaseModel):
    keyword: str

# 키워드 저장
@router.post("/save_keyword")
async def save_user_keyword(request: KeywordRequest, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    user_id = current_user['userId']

    # 키워드가 이미 존재하는지 확인
    db_keyword = db.query(Keyword).filter(Keyword.keyword == request.keyword).first()
    if not db_keyword:
        # 키워드가 없으면 새로 생성
        db_keyword = Keyword(keyword=request.keyword)
        db.add(db_keyword)
        db.commit()
        db.refresh(db_keyword)

    # 사용자가 이미 해당 키워드를 저장한 상태인지 확인
    existing_favorite = db.query(Favorite).filter(Favorite.userId == user_id, Favorite.keywordId == db_keyword.keywordId).first()
    if existing_favorite:
        raise HTTPException(status_code=400, detail="Keyword already saved")

    # 새로 Favorite 저장
    favorite = Favorite(userId=user_id, keywordId=db_keyword.keywordId)
    db.add(favorite)
    db.commit()
    db.refresh(favorite)

    return {"message": f"Keyword '{db_keyword.keyword}' saved successfully!"}

# 키워드 삭제
@router.delete("/delete_keyword")
async def delete_user_keyword(request: KeywordRequest, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    user_id = current_user['userId']

    # 해당 키워드가 저장되어 있는지 확인
    db_keyword = db.query(Keyword).filter(Keyword.keyword == request.keyword).first()
    if not db_keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")

    # 사용자가 해당 키워드를 즐겨찾기 한 상태인지 확인
    favorite = db.query(Favorite).filter(Favorite.userId == user_id, Favorite.keywordId == db_keyword.keywordId).first()
    if not favorite:
        raise HTTPException(status_code=400, detail="Keyword not found in user's favorites")

    # Favorite 삭제
    db.delete(favorite)
    db.commit()

    return {"message": f"Keyword '{request.keyword}' removed from favorites successfully!"}
