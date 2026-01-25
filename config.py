import os
from dotenv import load_dotenv
from pathlib import Path

#load environment variables from .env file
load_dotenv()

#Path
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
VECTOR_DB_DIR = BASE_DIR / "university_vector_db"

#----------------------------------------------------
# Models settings
#----------------------------------------------------
#embedding model
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DEVICE = "cpu"  # or "cuda" for GPU
#LLM model settings
LLM_provider = os.getenv("LLM_PROVIDER", "gemini") 
LLM_TEMPERATURE = 0.3
LLM_MAX_TOKENS = 4096
# Gemini model settings
GEMINI_MODEL = "gemini-flash-latest"
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")

#----------------------------------------------------
# Retriever settings
#----------------------------------------------------
# Vector search settings
RETRIEVAL_K = 5  # số lượng tài liệu hàng đầu để truy xuất
SIMILARITY_THRESHOLD = 0.5  # ngưỡng tương tự 
# Chunking settings
chunk_size = 500
chunk_overlap = 100
#----------------------------------------------------
# Chatbox settings
#----------------------------------------------------
# University info
UNIVERSITY_NAME = "Đại học Duy Tân"
UNIVERSITY_WEBSITE = "https://duytan.edu.vn"
ADMISSION_HOTLINE = "0236 3653 561"
ADMISSION_EMAIL = "tuyensinh@duytan.edu.vn"
# Chatbox behavior
enable_chat_history = True # bật/tắt lịch sử trò chuyện
max_chat_history_length = 10  # số lượng tin nhắn tối đa trong lịch sử trò chuyện
enable_source_citation = True  # hiển thị nguồn trích dẫn


#----------------------------------------------------
# STREAMLIT SETTINGS
PAGE_TITLE = f"🎓 Tư vấn Tuyển sinh - {UNIVERSITY_NAME}"
PAGE_ICON = "🎓"
LAYOUT = "wide"

#----------------------------------------------------
# Validation settings
#----------------------------------------------------
def validation(): # kiểm tra config hợp lệ
    error = []

    #check path
    if not DATA_DIR.exists():
        error.append(f"Đường dẫn data không hợp lê: {DATA_DIR}")
    #check api key
    if not GEMINI_API_KEY:
        error.append("API Key cho Google Gemini không được để trống.")

    if error:
        print("Lỗi cấu hình:")
        for e in error:
            print(f"- {e}")
        raise ValueError("Vui lòng kiểm tra lại cấu hình.")
    else:
        print("Cấu hình hợp lệ.")
    return len(error) == 0

if __name__ == "__main__":
    validation()





