from typing import Dict, Any
from ..state import GraphState
from database_utils import get_user_data # Proje ana dizinindeki dosyadan import ediyoruz

def get_user_profile(state: GraphState) -> Dict[str, Any]:
    """
    Fetches user data from the database based on user_id in the state.
    """
    print("---NODE: GET USER PROFILE---")
    user_id = state["user_id"]
    user_profile = get_user_data(user_id)

    if not user_profile:
        # Hata yönetimi: Eğer kullanıcı bulunamazsa ne yapılacağına karar verilebilir.
        # Şimdilik boş bir profil veya hata mesajı döndürebiliriz.
        raise ValueError(f"User with ID {user_id} not found in the database.")

    print(f"--- Found profile for user {user_id}: {user_profile} ---")

    return {"user_profile": user_profile}