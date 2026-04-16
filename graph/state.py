from typing import List, TypedDict


class GraphState(TypedDict):
    """
    RAG sisteminin hafızasında (state) tutulacak veriler.
    """
    # Dila'dan gelen temel veriler
    user_id: int
    question: str
    history: str

    # Dila'dan gelen fiziksel özellikler
    boy_cm: float
    kilo_kg: float
    yas: int
    cinsiyet: str
    
    # Dila'dan gelen o günkü beslenme verisi
    bugunku_ogunler: str

    # RAG sisteminin kendi ürettiği veriler
    documents: List[str]
    generation: str