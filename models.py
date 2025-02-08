from sqlalchemy import Column, Integer, String, ForeignKey, Date, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()  # SQLAlchemy ORM 모델의 기반 클래스

class User(Base):
    __tablename__ = 'users'  # MySQL 테이블 이름과 일치

    userId = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nickname = Column(String(50), nullable=False)
    userName = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False, unique=True)
    password = Column(String(255), nullable=False)  # 암호화된 비밀번호

    # 관계 설정: User는 여러 개의 Favorites를 가질 수 있음
    favorites = relationship("Favorite", back_populates="user")
    reports = relationship("Report", back_populates="user")


class Keyword(Base):
    __tablename__ = 'keywords'

    keywordId = Column(Integer, primary_key=True, index=True, autoincrement=True)
    keyword = Column(String(255), nullable=False, unique=True)

    # 관계 설정: Keyword는 여러 개의 Favorites와 Reports를 가질 수 있음
    favorites = relationship("Favorite", back_populates="keyword")
    reports = relationship("Report", back_populates="keyword")


class Favorite(Base):
    __tablename__ = 'favorites'

    favoriteId = Column(Integer, primary_key=True, index=True, autoincrement=True)
    userId = Column(Integer, ForeignKey('users.userId'), nullable=False)
    keywordId = Column(Integer, ForeignKey('keywords.keywordId'), nullable=False)

    # 관계 설정
    user = relationship("User", back_populates="favorites")
    keyword = relationship("Keyword", back_populates="favorites")


class Report(Base):
    __tablename__ = 'reports'

    reportId = Column(Integer, primary_key=True, index=True, autoincrement=True)
    userId = Column(Integer, ForeignKey('users.userId'), nullable=False)
    keywordId = Column(Integer, ForeignKey('keywords.keywordId'), nullable=False)
    reportDate = Column(Date, nullable=False)
    reportContent = Column(Text, nullable=True)
    isViewed = Column(Boolean, default=False)

    # 관계 설정
    user = relationship("User", back_populates="reports")
    keyword = relationship("Keyword", back_populates="reports")

    # UNIQUE 제약조건 설정: 하루에 한 번 보고서 생성
    __table_args__ = (
        UniqueConstraint('userId', 'keywordId', 'reportDate', name='_user_keyword_reportDate_uc'),
    )