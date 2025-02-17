from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, SessionLocal
from models import Keyword, Favorite, Report, User
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
    keywordId: int
    isViewed: bool

class UpdateReportRequest(BaseModel):
    reportId: int
    keyword: str
    reportDate: date
    keywordId: int
    reportContent: str
    isViewed: bool

class DeleteReportRequest(BaseModel):
    reportId: int

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

    # 사용자가 즐겨찾기한 키워드에 해당하는 리포트들 조회
    reports = db.query(Report).filter(Report.keywordId == db_keyword.keywordId, Report.userId == user_id).all()

    # 리포트 삭제 (해당 키워드와 관련된 모든 리포트)
    for report in reports:
        db.delete(report)
    
    # Favorite 삭제
    db.delete(favorite)
    db.commit()

    return {"message": f"Keyword '{request.keyword}' removed from favorites successfully!"}

class KeywordResponse(BaseModel):
    keyword: str

# 사용자가 즐겨찾기한 키워드 조회
@router.get("/favorites", response_model=List[KeywordResponse])
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
@router.get("/reports/{keyword}", response_model=List[ReportResponse])
async def get_reports_for_keyword(keyword: str, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    user_id = current_user['userId']

    # 사용자가 즐겨찾기한 키워드를 먼저 조회
    favorites = db.query(Favorite).filter(Favorite.userId == user_id).all()

    if not favorites:
        raise HTTPException(status_code=404, detail="No favorite keywords found")

    # 해당 키워드가 사용자의 즐겨찾기 목록에 있는지 확인
    db_keyword = db.query(Keyword).filter(Keyword.keyword == keyword).first()
    if not db_keyword:
        raise HTTPException(status_code=404, detail=f"Keyword '{keyword}' not found in user's favorites")

    # 해당 키워드에 대한 리포트 조회
    reports = db.query(Report).filter(Report.keywordId == db_keyword.keywordId, Report.userId == user_id).all()
    
    if not reports:
        raise HTTPException(status_code=404, detail="No reports found for the specified keyword")

    # 리포트 리스트 반환
    return [ReportResponse(
        reportId=report.reportId,
        keyword=db_keyword.keyword,
        keywordId=db_keyword.keywordId,
        reportDate=report.reportDate,
        reportContent=report.reportContent,
        isViewed=report.isViewed
    ) for report in reports]


# 리포트의 'isViewed' 상태 업데이트
@router.put("/update_report_viewed", response_model=ReportResponse)
async def update_report_viewed(request: UpdateReportRequest, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    try:
        print("Request Data:", request)
        user_id = current_user['userId']
        print(user_id)
        # 리포트 조회
        db_report = db.query(Report).filter(Report.reportId == request.reportId, Report.userId == user_id).first()
        print(db_report)

        if not db_report:
            raise HTTPException(status_code=404, detail="Report not found")

        db_report.keywordId = request.keywordId
        db_report.reportDate = request.reportDate
        db_report.reportContent = request.reportContent
        db_report.isViewed = request.isViewed

        # 리포트 상태 업데이트
        db.commit()
        db.refresh(db_report)
        db_keyword = db.query(Keyword).filter(Keyword.keywordId == db_report.keywordId).first()
        
        return ReportResponse(
            reportId=db_report.reportId,
            keyword=db_keyword.keyword,
            keywordId=db_keyword.keywordId,
            reportDate=db_report.reportDate,
            reportContent=db_report.reportContent,
            isViewed=db_report.isViewed
        )
    except Exception as e:
        print(f"Server Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


# 리포트 삭제
@router.delete("/delete_report", response_model=dict)
async def delete_report(request: DeleteReportRequest, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    user_id = current_user['userId']

    # 리포트 ID에 해당하는 리포트를 조회
    db_report = db.query(Report).filter(Report.reportId == request.reportId, Report.userId == user_id).first()

    if not db_report:
        raise HTTPException(status_code=404, detail="Report not found")

    # 리포트 삭제
    db.delete(db_report)
    db.commit()

    # 리포트 삭제 후 메시지 반환
    return {"message": f"Report with ID {request.reportId} deleted successfully!"}

    
@router.post("/generate_reports")
async def generate_reports():  # db는 Session 객체
    db = SessionLocal()

    # 모든 사용자의 정보를 가져옴
    all_users = db.query(User).all()  # User 모델이 존재한다고 가정

    # 각 사용자의 즐겨찾기 키워드에 대해 리포트를 생성
    new_reports = []
    today = date.today()

    for user in all_users:
        # 각 사용자의 즐겨찾기에 추가한 키워드 가져오기
        favorite_keywords = db.query(Favorite).filter(Favorite.userId == user.userId).all()

        # 즐겨찾기 키워드가 없다면 리포트 생성을 건너뛰기
        if not favorite_keywords:
            continue

        for favorite in favorite_keywords:
            keyword = db.query(Keyword).filter(Keyword.keywordId == favorite.keywordId).first()

            if keyword:
                new_report = Report(
                    userId=user.userId,
                    keywordId=keyword.keywordId,
                    reportDate=today,
                    reportContent=f"Generated report for keyword: {keyword.keyword}",
                    isViewed=False
                )
                db.add(new_report)
                new_reports.append(new_report)

    # 변경사항 커밋
    db.commit()

    return {"message": f"Reports generated for {len(new_reports)} keywords across all users."}

