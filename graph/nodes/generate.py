import json
from typing import Any, Dict
from ..chains.generation import generation_chain
from ..state import GraphState


def format_user_profile_for_prompt(state: GraphState) -> str:
    """
    Dila'dan State'e (hafızaya) gelen kullanıcı bilgilerini LLM'in anlayacağı bir metne dönüştürür.
    """
    # Dila'nın yolladığı verileri güvenli bir şekilde (.get ile) çekiyoruz
    yas = state.get("yas", "Belirtilmemiş")
    cinsiyet = state.get("cinsiyet", "Belirtilmemiş")
    boy_cm = state.get("boy_cm", "Belirtilmemiş")
    kilo_kg = state.get("kilo_kg", "Belirtilmemiş")

    # Dila'dan gelen sohbet geçmişi
    history = state.get("history", "Önceki konuşma geçmişi yok.")

    # Dila'dan gelen güncel yediklerinin özeti
    bugunku_ogunler = state.get("bugunku_ogunler", "Bugün henüz öğün bilgisi girilmemiş.")

    profile_text = (
        f"- Yaş: {yas}\n"
        f"- Cinsiyet: {cinsiyet}\n"
        f"- Boy: {boy_cm} cm\n"
        f"- Kilo: {kilo_kg} kg\n"
        f"- Bugün Yediği Öğünler: {bugunku_ogunler}\n"
        f"- Sohbet Geçmişi: {history}\n"
    )
    return profile_text


def generate(state: GraphState) -> Dict[str, Any]:
    print("---GENERATE PERSONALIZED ANSWER---")

    question = state["question"]
    documents = state["documents"]

    # 1. Kullanıcı profilini Dila'dan gelen State verisiyle formatla
    formatted_profile = format_user_profile_for_prompt(state)

    # 2. Senin önceden kurduğun generation_chain'i yeni girdilerle çağır
    generation = generation_chain.invoke({
        "context": documents,
        "question": question,
        "user_profile": formatted_profile
    })

    # 3. Sonucu dön
    return {"documents": documents, "question": question, "generation": generation}