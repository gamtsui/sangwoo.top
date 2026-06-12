from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Products(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    name_zh = Column(String(200))
    name_en = Column(String(200))
    description_zh = Column(Text)
    description_en = Column(Text)
    specifications = Column(JSON)
    images = Column(JSON)  # Array of image paths
    slug = Column(String(200), unique=True)
    price = Column(String(50))  # Price with currency (e.g., "₩15,000" or "¥128")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class News(Base):
    __tablename__ = 'news'
    id = Column(Integer, primary_key=True)
    title_zh = Column(String(300))
    title_en = Column(String(300))
    content_zh = Column(Text)
    content_en = Column(Text)
    slug = Column(String(200), unique=True)
    status = Column(String(20), default='draft')  # draft/published
    source = Column(String(100))  # manual/crawler
    created_at = Column(DateTime, default=datetime.now)
    published_at = Column(DateTime, nullable=True)

class SiteSettings(Base):
    __tablename__ = 'site_settings'
    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True)
    value = Column(JSON)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class AboutCompany(Base):
    __tablename__ = 'about_company'
    id = Column(Integer, primary_key=True)
    content_zh = Column(Text)
    content_en = Column(Text)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class Contact(Base):
    __tablename__ = 'contact'
    id = Column(Integer, primary_key=True)
    email = Column(String(100))
    phone = Column(String(50))
    address_zh = Column(Text)
    address_en = Column(Text)
    social_media = Column(JSON)
    form_enabled = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class VisitorSubmissions(Base):
    __tablename__ = 'visitor_submissions'
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    email = Column(String(100))
    subject = Column(String(200))
    message = Column(Text)
    created_at = Column(DateTime, default=datetime.now)

class Analytics(Base):
    __tablename__ = 'analytics'
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, default=datetime.now)
    page = Column(String(200))
    source = Column(String(100))
    user_agent = Column(Text)
    cookie_id = Column(String(50))

class SystemLog(Base):
    __tablename__ = 'system_log'
    id = Column(Integer, primary_key=True)
    level = Column(String(20))  # info/warning/error
    message = Column(Text)
    created_at = Column(DateTime, default=datetime.now)

class AdminSessions(Base):
    __tablename__ = 'admin_sessions'
    id = Column(Integer, primary_key=True)
    username = Column(String(50))
    token = Column(String(100), unique=True)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)
