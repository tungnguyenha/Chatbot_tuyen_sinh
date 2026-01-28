## 📌 Giới thiệu

Chatbot tư vấn tuyển sinh cho Trường Đại học Duy Tân, 
hỗ trợ thí sinh tra cứu thông tin về:
- Ngành học
- Điểm chuẩn
- Học phí
- Chương trình đào tạo
- Cơ hội nghề nghiệp

Hệ thống được xây dựng theo kiến trúc Retrieval-Augmented Generation (RAG),
kết hợp tìm kiếm ngữ nghĩa và dữ liệu có cấu trúc để đảm bảo câu trả lời chính xác.

## ✨ Tính năng

- 🤖 **AI-Powered**: Sử dụng Google gemini-flash-latest
- 📚 **RAG Architecture**: Kết hợp vector search + structured data
- 🔍 **Smart Retrieval**: Query routing và hybrid search
- 💬 **Chat Interface**: Giao diện Streamlit thân thiện
- 📊 **Source Citation**: Hiển thị nguồn tham khảo
- 🎯 **Query Types**: Tự động phân loại câu hỏi

## 📁 Cấu trúc Project

```
Chatbox_tuyensinh/
├── data/                      # Dữ liệu nguồn (JSON)
├── university_vector_db/      # Vector database (FAISS)
├── src/                       # Source code
│   ├── retriever.py          # Retrieval logic
│   ├── RAG_chatbot.py            # RAG chatbot
│   └── utils.py              # Utilities
├── UI/                       # Source code
│   ├── styles.py          # UI styles
│   ├── footer.py          # Footer component
│   ├── header.py          # Header component
│   ├── sidebar.py         # Sidebar navigation
│   └── chat.py            # Chat interface
├── app.py                     # Streamlit UI
├── config.py                  # Configuration
├── requirements.txt           # Dependencies
├── .env                       # API keys (không commit)
└── README.md                  # Documentation
```


## 🚀 Cài đặt

### 1. Clone hoặc tạo project structure

```bash
cd D:/Chatbox_tuyensinh
```

### 2. Tạo virtual environment

```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux
```

### 3. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### 4. Setup API Key

**Option A: File `.env`**
```bash
# Tạo file .env
echo GOOGLE_API_KEY=your_api_key_here > .env
```

**Option B: Environment Variable**
```bash
# Windows PowerShell
$env:GOOGLE_API_KEY="your_api_key_here"

# Mac/Linux
export GOOGLE_API_KEY="your_api_key_here"
```

**Option C: Streamlit Secrets** (cho deployment)
```bash
# Tạo .streamlit/secrets.toml
mkdir .streamlit
echo 'GOOGLE_API_KEY = "your_api_key_here"' > .streamlit/secrets.toml
```

### 5. Lấy Google Gemini API Key

1. Truy cập: https://aistudio.google.com/app/apikey
2. Click "Create API key in new project"
3. Copy API key (dạng `AIzaSy...`)

## 🎯 Sử dụng

### 1. Chạy Streamlit UI (Khuyến nghị)

```bash
streamlit run app.py
```


## ⚠️ Hạn chế hiện tại

- Dữ liệu được tổng hợp thủ công
- Chưa hỗ trợ multi-university

## 🚀 Hướng phát triển

- Crawl dữ liệu tuyển sinh tự động
- Hỗ trợ nhiều trường đại học
- Tối ưu prompt cho Gemini
