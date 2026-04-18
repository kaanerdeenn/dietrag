from dotenv import load_dotenv
load_dotenv()

import os
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List
from jose import jwt, JWTError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime
import httpx

import utils
import models
import schemas
from database import engine, SessionLocal

# =============================================
# KAAN'IN RAG YAPAY ZEKA GRAFİĞİNİ İMPORT ET
# =============================================
from graph.graph import app as rag_graph

# =============================================
# UYGULAMA KURULUMU
# =============================================

# Tabloları Supabase'de otomatik oluştur (ilk çalıştırmada)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Diyet Asistanı AI Servisi (Kaan + Dila)")

# CORS - Eylül'ün Android uygulamasının bağlanabilmesi için
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "Diyet Asistanı API başarıyla çalışıyor! (Render Health Check OK)"}

@app.head("/")
def home_head():
    return {"message": "Diyet Asistanı API başarıyla çalışıyor! (Render Health Check OK)"}

# =============================================
# GÜVENLİK & VERİTABANI BAĞLANTISI
# =============================================

security = HTTPBearer()

def get_db():
    """Her istekte yeni bir veritabanı oturumu açar, bitince kapatır."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """JWT token'ını kontrol eder ve giriş yapmış kullanıcıyı döner."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Giriş yapmanız gerekiyor (Token geçersiz)",
    )
    try:
        token = credentials.credentials
        payload = jwt.decode(token, utils.SECRET_KEY, algorithms=[utils.ALGORITHM])
        email: str | None = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

# =============================================
# 1. KAYIT OL (REGISTER)
# =============================================

@app.post("/users/", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Bu e-posta adresi zaten kayıtlı!")

    hashed_pwd = utils.hash_password(user.password)
    new_user = models.User(
        email=user.email,
        password_hash=hashed_pwd,
        full_name=user.full_name,
        boy_cm=user.boy_cm,
        kilo_kg=user.kilo_kg,
        yas=user.yas,
        cinsiyet=user.cinsiyet,
        language=user.language
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# =============================================
# 2. GİRİŞ YAP (LOGIN)
# =============================================

@app.post("/auth/login")
def login(user_credentials: schemas.LoginItem, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == user_credentials.email).first()

    if not user:
        # Test amaçlı: Kullanıcı yoksa otomatik oluştur
        hashed_pwd = utils.hash_password(user_credentials.password)
        new_user = models.User(
            email=user_credentials.email,
            password_hash=hashed_pwd,
            full_name="Otomatik Test Kullanıcısı"
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        user = new_user

    # Not: Şifre kontrolü test için devre dışı. Yayına almadan önce açın!
    # if not utils.verify_password(user_credentials.password, user.password_hash):
    #     raise HTTPException(status_code=403, detail="Şifre hatalı!")

    access_token = utils.create_access_token(
        data={"sub": user.email, "id": user.id}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "full_name": user.full_name,
    }

# =============================================
# 3. KULLANICI BİLGİ GÜNCELLEME (SETTINGS)
# =============================================

@app.post("/users/update/", response_model=schemas.UserResponse)
def update_user_me(
    user_update: schemas.UserUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Android Gson null olanları gönderdiği için None olmayanları filtreliyoruz
    update_data = {k: v for k, v in user_update.dict(exclude_unset=True).items() if v is not None}
    
    if "email" in update_data and update_data["email"] != current_user.email:
        existing_user = db.query(models.User).filter(models.User.email == update_data["email"]).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Bu e-posta adresi zaten kullanımda.")
            
    if "password" in update_data:
        pwd = update_data.pop("password")
        if pwd and str(pwd).strip():
            update_data["password_hash"] = utils.hash_password(pwd)

    for key, value in update_data.items():
        setattr(current_user, key, value)
        
    db.commit()
    db.refresh(current_user)
    return current_user

# =============================================
# 4. KULLANICI LİSTELE
# =============================================

@app.get("/users/", response_model=List[schemas.UserResponse])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users

# =============================================
# 5. YEMEK KAYDETME & LİSTELEME
# =============================================

@app.post("/meals/", response_model=schemas.MealResponse)
def create_meal(
    meal: schemas.MealCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    new_meal = models.Meal(**meal.dict(), user_id=current_user.id)
    db.add(new_meal)
    db.commit()
    db.refresh(new_meal)
    return new_meal

@app.get("/meals/", response_model=List[schemas.MealResponse])
def read_meals(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    meals = db.query(models.Meal).filter(models.Meal.user_id == current_user.id).all()
    return meals

# =============================================
# 6. SU TAKİBİ
# =============================================

@app.post("/water/", response_model=schemas.WaterResponse)
def create_water_log(
    water: schemas.WaterCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    new_water = models.WaterLog(amount_ml=water.amount_ml, user_id=current_user.id)
    db.add(new_water)
    db.commit()
    db.refresh(new_water)
    return new_water

@app.get("/water/", response_model=List[schemas.WaterResponse])
def read_water_logs(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    water_logs = db.query(models.WaterLog).filter(models.WaterLog.user_id == current_user.id).all()
    return water_logs

# =============================================
# 7. CHATBOT (KAAN'IN RAG SİSTEMİ - DOĞRUDAN)
# =============================================

@app.post("/chat")
def chat_with_ai(
    chat_request: schemas.ChatRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Android'den gelen soruyu alır, RAG Yapay Zeka sistemine doğrudan sorar,
    cevabı veritabanına kaydeder ve Android'e geri döner.
    """
    # Mesajı al (Android'in user_message veya Dila'nın message formatını destekle)
    message = chat_request.user_message or chat_request.message
    if not message:
        raise HTTPException(status_code=400, detail="Bir mesaj yazmanız gerekiyor.")

    # Öğün bilgisini string formatına çevir (RAG'ın beklediği format)
    ogunler_str = ""
    if chat_request.bugunku_ogunler:
        for ogun in chat_request.bugunku_ogunler:
            ogunler_str += f"- {ogun.food_name} ({ogun.calories} kcal, Protein: {ogun.protein}g, Yağ: {ogun.fat}g, Karb: {ogun.carbs}g)\n"
    else:
        # Eğer Android öğün göndermemişse, veritabanından son 5 öğünü çek
        last_meals = db.query(models.Meal).filter(models.Meal.user_id == current_user.id).order_by(models.Meal.created_at.desc()).limit(5).all()
        for m in last_meals:
            ogunler_str += f"- {m.food_name} ({m.calories} kcal)\n"

    if not ogunler_str:
        ogunler_str = "Bugün henüz öğün girilmemiş."

    # Kullanıcı bilgilerini al (Android'in default Kadın göndermesini ezip veritabanını önceliklendir)
    boy = getattr(current_user, 'boy_cm', None) or chat_request.boy_cm or 170.0
    kilo = getattr(current_user, 'kilo_kg', None) or chat_request.kilo_kg or 70.0
    yas = getattr(current_user, 'yas', None) or chat_request.yas or 30
    
    db_cinsiyet = getattr(current_user, 'cinsiyet', None)
    cinsiyet = db_cinsiyet if db_cinsiyet and db_cinsiyet != "Belirtilmemiş" else (chat_request.cinsiyet or "Belirtilmemiş")

    print(f"🤖 Chat İsteği -> Kullanıcı: {current_user.email} | Boy: {boy} | Kilo: {kilo} | Mesaj: {message[:50]}...")

    # ============================================
    # RAG YAPAY ZEKA GRAFİĞİNİ DOĞRUDAN ÇAĞIR
    # (Artık proxy yok, doğrudan Kaan'ın kodu çalışıyor!)
    # ============================================
    try:
        user_input = {
            "user_id": current_user.id,
            "question": message,
            "history": chat_request.history,
            "boy_cm": boy,
            "kilo_kg": kilo,
            "yas": yas,
            "cinsiyet": cinsiyet,
            "bugunku_ogunler": ogunler_str,
        }
        final_result = rag_graph.invoke(user_input)
        ai_reply = final_result.get("generation", "AI cevap üretemedi.")

    except Exception as e:
        print(f"❌ RAG Hatası: {e}")
        ai_reply = f"Yapay zeka şu an meşgul. Lütfen tekrar deneyin."

    # Sohbeti veritabanına kaydet (Dila'nın ChatLog tablosu)
    try:
        new_chat = models.ChatLog(
            user_id=current_user.id,
            user_message=message,
            bot_response=ai_reply
        )
        db.add(new_chat)
        db.commit()
    except Exception as e:
        print(f"⚠️ Chat log kaydedilemedi: {e}")

    return {"reply": ai_reply}

# =============================================
# 8. YEMEK ANALİZ (FOTOĞRAF -> KALORİ)
# =============================================

MEHMET_AI_URL = os.getenv("MEHMET_AI_URL", "http://192.168.1.11:8000/analyze")

@app.post("/analyze")
async def analyze_food(
    file: UploadFile = File(...)
):
    """Fotoğraftan yemek tanıma - Mehmet'in yapay zeka servisine proxy."""
    image_data = await file.read()
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                MEHMET_AI_URL,
                files={"file": (file.filename, image_data, file.content_type)},
                timeout=90.0
            )
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": "AI servisi cevap veremedi."}
        except Exception as e:
            print(f"⚠️ Yemek Analiz Hatası (Mehmet sunucusu kapalı olabilir): {e}")
            return {
                "food_name": "Demo Yemek (AI Kapalı)",
                "calories": 350,
                "protein": 20,
                "fat": 10,
                "carbs": 40,
                "note": "Mehmet'in sunucusu kapalı olduğu için demo veri döndü."
            }

# =============================================
# 9. TARİF ÖNERİSİ (NE YESEM?)
# =============================================

@app.post("/recommend-recipes")
async def forward_to_ai_agent(file: UploadFile = File(...)):
    """Fotoğraftaki malzemeleri tanıyıp tarif öneren endpoint."""
    try:
        file_bytes = await file.read()
        async with httpx.AsyncClient(timeout=90.0) as client:
            files = {"file": (file.filename, file_bytes, file.content_type)}
            response = await client.post(MEHMET_AI_URL, files=files)
            
            if response.status_code == 200:
                return JSONResponse(content=response.json())
            else:
                error_detail = response.text if response.text else "AI sunucusunda hata oluştu."
                raise HTTPException(status_code=response.status_code, detail=f"AI Hatası: {error_detail}")
                
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Mehmet'in AI sunucusuna bağlanılamıyor.")
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="AI sunucusu 90 saniye içinde cevap vermedi.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =============================================
# SUNUCU BAŞLATMA
# =============================================

import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run(app, host="0.0.0.0", port=port)