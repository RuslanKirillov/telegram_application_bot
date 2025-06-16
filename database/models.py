from sqlalchemy import Column, Integer, String, Boolean, DateTime, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Application(Base):
    __tablename__ = 'applications'
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=False)  # заменили Integer на BigInteger
    username = Column(String(100))
    first_name = Column(String(100), nullable=False)
    phone_number = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    admin_id = Column(Integer)
    closed_at = Column(DateTime)

class AdminActionLog(Base):
    __tablename__ = 'admin_actions'
    id = Column(Integer, primary_key=True)
    admin_id = Column(Integer, nullable=False)
    admin_username = Column(String(100))
    action = Column(String(255), nullable=False)
    application_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
