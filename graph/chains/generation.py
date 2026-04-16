from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

# Kişiselleştirilmiş cevaplar için yeni prompt şablonu
PERSONALIZED_PROMPT_TEMPLATE = """Sen, kullanıcıların kişisel sağlık ve beslenme verilerine dayanarak onlara tavsiyeler veren uzman bir diyet asistanısın. Amacın, sana verilen bağlamı (retrieved documents) ve kullanıcının profil bilgilerini birleştirerek sorularına kişiselleştirilmiş, destekleyici ve bilimsel temelli cevaplar vermektir.

**Kullanıcı Profili:**
{user_profile}

**Bağlam (Bilgi Kaynakları):**
{context}

**Kullanıcı Sorusu:**
{question}

Yukarıdaki bilgileri kullanarak kullanıcının sorusuna cevap ver. Cevabını verirken doğrudan kullanıcıya hitap et ve profil bilgilerini (örneğin, günlük aldığı kalori miktarı, yaşı, kilosu vb.) doğal bir şekilde cevabına dahil et.
"""

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.5) # Yaratıcılığı artırmak için sıcaklığı biraz yükseltebiliriz
prompt = ChatPromptTemplate.from_template(PERSONALIZED_PROMPT_TEMPLATE)

generation_chain = prompt | llm | StrOutputParser()