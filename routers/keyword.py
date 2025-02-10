from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Keyword, Favorite, Report
from auth import get_current_user
from pydantic import BaseModel
from datetime import date
from typing import List

router = APIRouter()

class KeywordRequest(BaseModel):
    keyword: str

class ReportResponse(BaseModel):
    reportId: int
    keyword: str
    reportDate: date
    reportContent: str
    isViewed: bool

class UpdateReportRequest(BaseModel):
    reportId: int
    isViewed: bool

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

class KeywordResponse(BaseModel):
    keyword: str

# 사용자가 즐겨찾기한 키워드 조회
@router.get("/favorites", response_model=list[KeywordResponse])
async def get_user_favorites(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    user_id = current_user['userId']
    
    # 사용자가 즐겨찾기한 키워드 목록을 조회
    favorites = db.query(Favorite).filter(Favorite.userId == user_id).all()
    
    if not favorites:
        raise HTTPException(status_code=404, detail="No favorite keywords found")

    # 키워드 정보를 반환
    keyword_list = []
    for favorite in favorites:
        db_keyword = db.query(Keyword).filter(Keyword.keywordId == favorite.keywordId).first()
        if db_keyword:
            keyword_list.append(KeywordResponse(keyword=db_keyword.keyword))

    return keyword_list
    
# 사용자가 즐겨찾기한 키워드에 대한 리포트 조회
@router.get("/reports", response_model=List[ReportResponse])
async def get_user_reports(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    user_id = current_user['userId']

    # 사용자가 즐겨찾기한 키워드를 먼저 조회
    favorites = db.query(Favorite).filter(Favorite.userId == user_id).all()
    
    if not favorites:
        raise HTTPException(status_code=404, detail="No favorite keywords found")

    # 즐겨찾기한 키워드에 대한 리포트 목록 조회
    reports = []
    for favorite in favorites:
        db_keyword = db.query(Keyword).filter(Keyword.keywordId == favorite.keywordId).first()
        if db_keyword:
            # 해당 키워드에 대한 리포트 조회
            db_reports = db.query(Report).filter(Report.keywordId == db_keyword.keywordId, Report.userId == user_id).all()
            for report in db_reports:
                reports.append(ReportResponse(
                    reportId=report.reportId,
                    keyword=db_keyword.keyword,
                    reportDate=report.reportDate,
                    reportContent=report.reportContent,
                    isViewed=report.isViewed
                ))

    if not reports:
        raise HTTPException(status_code=404, detail="No reports found for your favorite keywords")

    return reports

# 리포트의 'isViewed' 상태 업데이트
@router.put("/update_report_viewed", response_model=ReportResponse)
async def update_report_viewed(request: UpdateReportRequest, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    user_id = current_user['userId']

    # 리포트 ID에 해당하는 리포트를 조회
    db_report = db.query(Report).filter(Report.reportId == request.reportId, Report.userId == user_id).first()

    if not db_report:
        raise HTTPException(status_code=404, detail="Report not found")

    # 리포트의 'isViewed' 상태 업데이트
    db_report.isViewed = request.isViewed
    db.commit()
    db.refresh(db_report)

    # 리포트 상태 업데이트 후 반환
    return ReportResponse(
        reportId=db_report.reportId,
        keyword=db_report.keyword,  
        reportDate=db_report.reportDate,
        reportContent=db_report.reportContent, 
        isViewed=db_report.isViewed 
    )
