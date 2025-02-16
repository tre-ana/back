from sqlalchemy import Column, Integer, String, ForeignKey, Date, Text, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()  # SQLAlchemy ORM 모델의 기반 클래스

class User(Base):
    __tablename__ = 'Users'  # MySQL 테이블 이름과 일치

    userId = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nickname = Column(String(50), nullable=False)
    userName = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False, unique=True)
    password = Column(String(255), nullable=False)  # 암호화된 비밀번호

    # 관계 설정: User는 여러 개의 Favorites를 가질 수 있음
    favorites = relationship("Favorite", back_populates="user")
    reports = relationship("Report", back_populates="user")


class Keyword(Base):
    __tablename__ = 'Keywords'

    keywordId = Column(Integer, primary_key=True, index=True, autoincrement=True)
    keyword = Column(String(255), nullable=False, unique=True)

    favorites = relationship("Favorite", back_populates="keyword")
    reports = relationship("Report", back_populates="keyword")


class Favorite(Base):
    __tablename__ = 'Favorites'

    favoriteId = Column(Integer, primary_key=True, index=True, autoincrement=True)
    userId = Column(Integer, ForeignKey('Users.userId'), nullable=False)
    keywordId = Column(Integer, ForeignKey('Keywords.keywordId'), nullable=False)

    user = relationship("User", back_populates="favorites")
    keyword = relationship("Keyword", back_populates="favorites")


class Report(Base):
    __tablename__ = 'Reports'

    reportId = Column(Integer, primary_key=True, index=True, autoincrement=True)
    userId = Column(Integer, ForeignKey('Users.userId'), nullable=False)
    keywordId = Column(Integer, ForeignKey('Keywords.keywordId'), nullable=False)
    reportDate = Column(Date, nullable=False)
    reportContent = Column(Text, nullable=True)
    isViewed = Column(Boolean, default=False)

    user = relationship("User", back_populates="reports")
    keyword = relationship("Keyword", back_populates="reports")

    __table_args__ = (
        UniqueConstraint('userId', 'keywordId', 'reportDate', name='_user_keyword_reportDate_uc'),
    )
