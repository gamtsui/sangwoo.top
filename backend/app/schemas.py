from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# --- Products ---
class ProductCreate(BaseModel):
    name_zh: Optional[str] = None
    name_en: Optional[str] = None
    description_zh: Optional[str] = None
    description_en: Optional[str] = None
    specifications: Optional[dict] = None
    images: Optional[list] = None
    slug: Optional[str] = None
    is_active: bool = True


class ProductUpdate(BaseModel):
    name_zh: Optional[str] = None
    name_en: Optional[str] = None
    description_zh: Optional[str] = None
    description_en: Optional[str] = None
    specifications: Optional[dict] = None
    images: Optional[list] = None
    slug: Optional[str] = None
    is_active: Optional[bool] = None


# --- News ---
class NewsCreate(BaseModel):
    title_zh: Optional[str] = None
    title_en: Optional[str] = None
    content_zh: Optional[str] = None
    content_en: Optional[str] = None
    slug: Optional[str] = None
    status: str = 'draft'
    source: Optional[str] = None


class NewsUpdate(BaseModel):
    title_zh: Optional[str] = None
    title_en: Optional[str] = None
    content_zh: Optional[str] = None
    content_en: Optional[str] = None
    slug: Optional[str] = None
    status: Optional[str] = None
    source: Optional[str] = None


# --- SiteSettings ---
class SettingCreate(BaseModel):
    key: str
    value: Optional[dict] = None


class SettingUpdate(BaseModel):
    value: Optional[dict] = None


# --- AboutCompany ---
class AboutCreate(BaseModel):
    content_zh: Optional[str] = None
    content_en: Optional[str] = None


class AboutUpdate(BaseModel):
    content_zh: Optional[str] = None
    content_en: Optional[str] = None


# --- Contact ---
class ContactCreate(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    address_zh: Optional[str] = None
    address_en: Optional[str] = None
    social_media: Optional[dict] = None
    form_enabled: bool = True


class ContactUpdate(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    address_zh: Optional[str] = None
    address_en: Optional[str] = None
    social_media: Optional[dict] = None
    form_enabled: Optional[bool] = None


# --- VisitorSubmissions ---
class SubmissionCreate(BaseModel):
    name: str
    email: str
    subject: Optional[str] = None
    message: str


class SubmissionUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    subject: Optional[str] = None
    message: Optional[str] = None


# --- Analytics ---
class AnalyticsCreate(BaseModel):
    page: Optional[str] = None
    source: Optional[str] = None
    user_agent: Optional[str] = None
    cookie_id: Optional[str] = None


class AnalyticsUpdate(BaseModel):
    page: Optional[str] = None
    source: Optional[str] = None
    user_agent: Optional[str] = None
    cookie_id: Optional[str] = None


# --- SystemLog ---
class SystemLogCreate(BaseModel):
    level: str = 'info'
    message: str


class SystemLogUpdate(BaseModel):
    level: Optional[str] = None
    message: Optional[str] = None
