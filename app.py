import streamlit as st
from pathlib import Path
import sys
import os
sys.path.append(str(Path(__file__).parent))

from src.RAG_Chatbox import AdmissionChatbot
from src.utils import format_source, truncate_text
from config import *
from UI.components.styles import inject_css
from UI.components.header import render_header
from UI.components.sidebar import render_sidebar
from UI.components.footer import render_footer
from UI.components.chat import render_Chat_history, handle_chat_input
# ============================================
# PAGE CONFIG
# ============================================
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon= PAGE_ICON,
    layout= LAYOUT,
    initial_sidebar_state= "expanded"
)

# ============================================
# CUSTOM CSS
# ============================================
inject_css()


# ============================================
# INITIALIZE CHATBOT
# ============================================
def load_chatbot():
    """Load chatbot (cached)"""
    try:
        # Try to get API key from Streamlit secrets first
        api_key = (
            st.secrets.get("GOOGLE_API_KEY")
            if "GOOGLE_API_KEY" in st.secrets
            else os.getenv("GOOGLE_API_KEY")
            )
        chatbot = AdmissionChatbot(api_key=api_key)
        return chatbot, None
    except Exception as e:
        return None, str(e)

# ============================================
# SESSION STATE
# ============================================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "show_sources" not in st.session_state:
    st.session_state.show_sources = False
if "total_queries" not in st.session_state:
    st.session_state.total_queries = 0


# ============================================
# HEADER
# ============================================

render_header(PAGE_ICON, UNIVERSITY_NAME)

# ============================================
# SIDEBAR
# ============================================
render_sidebar(
    example_questions=[
        "Ngành Du lịch học những gì?",
        "Điểm chuẩn ngành Trí tuệ nhân tạo năm 2024?",
        "Xét tuyển ngành markerting bằng cách nào?",
        "Học phí khoa học dữ liệu bao nhiêu?"
    ],
    hotline=ADMISSION_HOTLINE,
    email=ADMISSION_EMAIL,
    website=UNIVERSITY_WEBSITE
)


# ============================================
# MAIN CHAT INTERFACE
# ============================================

chatbot,error = load_chatbot()

if error:
    st.error(f"""
    ❌ **Không thể khởi tạo chatbot**
    
    Lỗi: {error}
    
    **Khắc phục:**
    1. Kiểm tra file `.env` có `GOOGLE_API_KEY`
    2. Hoặc thêm API key vào `.streamlit/secrets.toml`:
       ```
       GOOGLE_API_KEY = "your-api-key"
       ```
    3. Lấy API key tại: https://aistudio.google.com/app/apikey
    """)
    st.stop()
if not st.session_state.messages:
    st.session_state.messages.append({
        "role": "assistant",
        "content": chatbot.get_welcome_message()
    })
# ============================================
# FOOTER
# ============================================
render_Chat_history()
handle_chat_input(chatbot)
render_footer(UNIVERSITY_NAME)