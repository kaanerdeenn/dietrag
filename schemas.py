from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# ========================
# KULLANICI ŞEMALARI
# ========================

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None
    boy_cm: Optional[float] = 170.0
    kilo_kg: Optional[float] = 70.0
    yas: Optional[int] = 30
    cinsiyet: Optional[str] = "Belirtilmemiş"
    language: Optional[str] = "English"

class LoginItem(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    boy_cm: Optional[float] = None
    kilo_kg: Optional[float] = None
    yas: Optional[int] = None
    cinsiyet: Optional[str] = None
    language: Optional[str] = None

    class Config:
        orm_mode = True
        from_attributes = True

class UserUpdate(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = None
    full_name: Optional[str] = None
    boy_cm: Optional[float] = None
    kilo_kg: Optional[float] = None
    yas: Optional[int] = None
    cinsiyet: Optional[str] = None
    language: Optional[str] = None

# ========================
# YEMEK ŞEMALARI
# ========================

class MealCreate(BaseModel):
    food_name: str
    calories: float
    protein: Optional[float] = 0
    fat: Optional[float] = 0
    carbs: Optional[float] = 0

class MealResponse(MealCreate):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True

# ========================
# SU TAKİBİ ŞEMALARI
# ========================

class WaterCreate(BaseModel):
    amount_ml: int

class WaterResponse(BaseModel):
    id: int
    user_id: int
    amount_ml: int
    created_at: datetime

    class Config:
        from_attributes = True

# ========================
# CHATBOT ŞEMALARI (Android uyumlu)
# ========================

class MealItem(BaseModel):
    food_name: str
    calories: float = 0.0
    protein: float = 0.0
    fat: float = 0.0
    carbs: float = 0.0

class ChatRequest(BaseModel):
    """Android'in gönderdiği sohbet isteği formatı"""
    user_id: int = 0
    user_message: str = ""
    message: str = ""          # Dila'nın eski formatıyla uyumluluk
    history: str = ""
    boy_cm: float = 170.0
    kilo_kg: float = 70.0
    yas: int = 30
    cinsiyet: str = "Belirtilmemiş"
    bugunku_ogunler: List[MealItem] = []
