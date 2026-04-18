from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt
import os

# --- GÜVENLİK AYARLARI ---
SECRET_KEY = os.getenv("SECRET_KEY", "bu-cok-gizli-ve-uzun-bir-anahtardir-kimseyle-paylasma")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 43200  # Token süresi 30 güne çıkarıldı (Android'de 401 hatasını önlemek için)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 1. Şifre Hashleme
def hash_password(password: str):
    return pwd_context.hash(password)

# 2. Şifre Doğrulama
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# 3. Token Oluşturma
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
