from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
import uvicorn

# 2. LangGraph Uygulamasını Import Etme
from graph.graph import app as rag_graph

app = FastAPI(title="Diyet Asistanı AI Servisi (Kaan)")

# =================================================================
# DİLA'NIN GÖNDERECEĞİ YENİ VERİ FORMATI
# =================================================================
from typing import List, Optional

class MealItem(BaseModel):
    food_name: str
    calories: float = 0.0
    protein: float = 0.0
    fat: float = 0.0
    carbs: float = 0.0

class ChatIstegi(BaseModel):
    user_id: int
    user_message: str
    history: str = ""
    boy_cm: Optional[float] = 170.0
    kilo_kg: Optional[float] = 70.0
    yas: Optional[int] = 30
    cinsiyet: Optional[str] = "Belirtilmemiş"
    bugunku_ogunler: Optional[List[MealItem]] = []

@app.post("/chat")
def chat_ile_cevapla(istek: ChatIstegi):
    try:
        # Geçmiş öğünleri (PostgreSQL'den gelen ham JSON array'ini) okunabilir bir stringe çevirme
        ogunler_str = ""
        if istek.bugunku_ogunler:
            for ogun in istek.bugunku_ogunler:
                ogunler_str += f"- {ogun.food_name} ({ogun.calories} kcal, Protein: {ogun.protein}g, Yağ: {ogun.fat}g, Karb: {ogun.carbs}g)\n"
        else:
            ogunler_str = "Bugün henüz öğün girilmemiş."

        print(f"Gelen İstek -> ID: {istek.user_id} | Boy: {istek.boy_cm} | Kilo: {istek.kilo_kg} | Öğünler Eklendi: {len(istek.bugunku_ogunler)} adet")

        # LangGraph için input hazırlığı
        # Artık veritabanına gitmek yerine, tüm fiziksel özellikleri Graph'a "state" olarak veriyoruz.
        user_input = {
            "user_id": istek.user_id,
            "question": istek.user_message,
            "history": istek.history,
            "boy_cm": istek.boy_cm,
            "kilo_kg": istek.kilo_kg,
            "yas": istek.yas,
            "cinsiyet": istek.cinsiyet,
            "bugunku_ogunler": ogunler_str,
        }

        # Grafiği çalıştır
        final_result = rag_graph.invoke(user_input)

        # Grafikten gelen cevabı al
        cevap_metni = final_result.get("generation", "Bir hata oluştu, cevap üretilemedi.")

        return {"reply": cevap_metni}

    except Exception as e:
        print(f"Sunucu Hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

import os
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run(app, host="0.0.0.0", port=port)