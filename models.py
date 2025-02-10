from sqlalchemy import Column, TEXT, INT, BIGINT
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Users(Base):
    __tablename__ = "users"

    user_id = Column(TEXT, primary_key=True)
    username = Column(TEXT, nullable=False)
    email = Column(TEXT, nullable=False)
    password = Column(TEXT, nullable=False)
    
    