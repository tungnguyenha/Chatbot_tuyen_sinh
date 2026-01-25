import os
from typing import List, Any, Optional, Dict
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_google_genai import ChatGoogleGenerativeAI

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from config import (GEMINI_MODEL, GEMINI_API_KEY, LLM_TEMPERATURE, LLM_MAX_TOKENS, UNIVERSITY_NAME,
                    ADMISSION_EMAIL, ADMISSION_HOTLINE, UNIVERSITY_WEBSITE )

from src.retriever import University_Retrieve
from src.utils import format_source

class AdmissionChatbot:
    #khởi tạo tham số
    def __init__(self, vector_db_path: str = None, api_key: str = None, enable_history: bool = True):
        print("🚀 Initializing Admission Chatbot...")
        # Retriever
        self.retriever = University_Retrieve(vector_db_path)

        print("🤖 Connecting to Gemini...")
        # Load LLM
        self.llm = ChatGoogleGenerativeAI(model=GEMINI_MODEL,
                                          temperature=LLM_TEMPERATURE,
                                          max_output_tokens=LLM_MAX_TOKENS,
                                          google_api_key= api_key or GEMINI_API_KEY,
                                          )
        print("✅ Gemini connected!")
        # Load prompt
        self.prompt = self._create_prompt_template()

        # RAG chain
        self.rag_chain = (
            {"context": self._retriever_context,"question": RunnablePassthrough()}
            | self.prompt
            | self.llm
            | StrOutputParser()
        )
        #chat history
        self.enable_history = enable_history
        self.history: List[Dict] = []
        print("✅ Chatbot ready!\n")
    
    
    # tạo template    
    def _create_prompt_template(self) -> ChatPromptTemplate:
        system_prompt = f"""Bạn là trợ lý tư vấn tuyển sinh thân thiện và chuyên nghiệp của {UNIVERSITY_NAME}.

                            🎯 NHIỆM VỤ:
                            - Tư vấn về ngành học, chương trình đào tạo, cơ hội nghề nghiệp
                            - Cung cấp thông tin điểm chuẩn, học phí, phương thức xét tuyển
                            - Giải đáp thắc mắc của thí sinh và phụ huynh
                            - Hỗ trợ định hướng nghề nghiệp

                            📋 QUY TẮC QUAN TRỌNG:
                            1. ✅ ƯU TIÊN sử dụng thông tin từ CONTEXT bên dưới
                            2. ❌ TUYỆT ĐỐI KHÔNG BỊA ĐẶT nếu không có trong CONTEXT
                            3. 📊 Với số liệu (điểm, học phí), phải CHÍNH XÁC tuyệt đối
                            4. ❓ Nếu thiếu thông tin, thừa nhận và gợi ý cách tìm hiểu
                            5. 🎯 Trả lời ngắn gọn (3-5 đoạn), dễ hiểu, thân thiện
                            6. 💡 Kết thúc bằng câu hỏi gợi ý hoặc call-to-action

                            🎨 PHONG CÁCH TRẢ LỜI:
                            - Dùng emoji phù hợp (📚 🎓 💰 📊 ⭐)
                            - Chia thành các đoạn ngắn, dễ đọc
                            - Dùng bullet points khi liệt kê
                            - Tone thân thiện nhưng chuyên nghiệp
                            - Tránh văn phong quá trang trọng

                            📞 THÔNG TIN LIÊN HỆ (khi cần):
                            - Hotline: {ADMISSION_HOTLINE}
                            - Email: {ADMISSION_EMAIL}
                            - Website: {UNIVERSITY_WEBSITE}

                            ---

                            CONTEXT (Thông tin từ cơ sở dữ liệu):
                            {{context}}

                            ---

                            ⚠️ NẾU KHÔNG CÓ THÔNG TIN:
                            "Xin lỗi, hiện tại tôi chưa có thông tin chi tiết về vấn đề này. 
                            Để được tư vấn chính xác hơn, bạn có thể:
                            📞 Gọi hotline: {ADMISSION_HOTLINE}
                            📧 Email: {ADMISSION_EMAIL}
                            🌐 Truy cập: {UNIVERSITY_WEBSITE}

                            Hoặc bạn có thể hỏi tôi về các chủ đề khác như ngành học, điểm chuẩn, học phí nhé! 😊"
                           """
        human_prompt = """Câu hỏi: {question}

                        Trả lời (bằng tiếng Việt, thân thiện, có cấu trúc rõ ràng):"""
        return ChatPromptTemplate.from_messages([("system", system_prompt),("human", human_prompt)])
    
    # lấy context từ retriever
    def _retriever_context(self, question:str) -> str:
        result = self.retriever.hybrid_search(query= question,k=5)
        return result['context']
    
    # thêm vào chat history
    def _add_to_history(self, role:str, content:str):
        if self.enable_history:
            self.history.append({"role":role, "content":content})

            if len(self.history) > 20:
                self.history = self.history[:-20]
    
    # ============================================
    # MAIN CHAT METHODS
    # ============================================

    # trả lời câu hỏi đơn giản
    def simple_chat(self, question: str) -> str:
        try:
            response = self.rag_chain.invoke(question)
            
            # lưu vào lịch sử chat
            self._add_to_history("user", question)
            self._add_to_history("assistant",response)
            return response
        except Exception as e:
            error_message = f"❌ Xin lỗi, có lỗi xảy ra: {str(e)}\n\nVui lòng thử lại hoặc liên hệ {ADMISSION_HOTLINE}"
        return error_message
    
    # chat với thông tin chi tiếc
    def chat_detailed(self, question: str) -> Dict:
        """
        Returns:
            {
                'answer': str,
                'sources': List[Document],
                'query_type': str,
                'confidence': str,
                'num_sources': int
            }
        """
        try:
            #retriever
            retriever_result = self.retriever.hybrid_search(query=question, k=5)

            # generate response
            answer = self.rag_chain.invoke(question)
            # estimate confidence
            num_sources = len(retriever_result['semantic_results'])
            if num_sources >= 3:
                    confidence = "Cao ✅"
            elif num_sources >= 1:
                confidence = "Trung bình ⚠️"
            else:
                confidence = "Thấp ❌"

            # save history
            self._add_to_history("user",question)
            self._add_to_history("assistant",answer)
            return{
                'answer': answer,
                'sources': retriever_result['semantic_results'],
                'query_type': retriever_result['query_type'],
                'confidence' : confidence,
                'num_sources' : num_sources
            }
        except Exception as e:
            return {
                'answer': f"❌ Lỗi: {str(e)}",
                'sources': [],
                'query_type': 'error',
                'confidence': 'N/A',
                'num_sources': 0,
                'structured_data': None
            }
    
    # chat với streaming(thể hiện từng từ trong streamlit)
    def chat_stream(self, question: str):

        try:
            # retriever context
            context = self._retriever_context(question)

            #create answers
            messages = self.prompt.format_messages(
                context = context,
                question = question
            )

            #stream response
            full_response =""
            for chunk in self.llm.stream(messages):
                if hasattr(chunk,'content'):
                    full_response += chunk.content
                    yield chunk.content

            # save history
            self._add_to_history("user",question)
            self._add_to_history("assistant",full_response)
        except Exception as e:
            yield f"❌ Lỗi: {str(e)}"
    # ============================================
    # UTILITY METHODS
    # ============================================

    # xoá chat history
    def reset_history(self):
        self.history = []
    
    # lấy lịch sử chat
    def get_history(self) -> List[Dict]:
        return self.history
    
    # lấy lời chào đầu tiên
    def get_welcome_message(self)-> str:
        return f"""Xin chào! 👋 Tôi là trợ lý tư vấn tuyển sinh của {UNIVERSITY_NAME}.
                    Tôi có thể giúp bạn về:
                    📚 Thông tin các ngành học và chương trình đào tạo
                    📊 Điểm chuẩn các năm trước
                    💰 Học phí và học bổng
                    📝 Phương thức xét tuyển
                    ❓ Các câu hỏi thường gặp

                    Bạn muốn tôi tư vấn về vấn đề gì? 😊"""


    # ============================================
    # TESTING
    # ============================================


def test_chatbot():
    print("\n🧪 Testing Chatbot...\n")

    # check API key
    if not GEMINI_API_KEY:
        print("❌ Chưa set GOOGLE_API_KEY")
        print("💡 Set trong .env hoặc environment variable")
        return
    
    try:
        chatbot = AdmissionChatbot()
    except Exception as e:
        print(f"❌ Lỗi khởi tạo: {e}")
        return
    # Test queries
    test_queries = [
        "Ngành du lịch học những môn gì?",
        "Điểm chuẩn trí tuệ nhân tạo năm 2024",
        "Học phí trí tuệ nhân tạo bao nhiêu?"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*70}")
        print(f"Test {i}/{len(test_queries)}")
        print(f"{'='*70}")
        print(f"🙋 User: {query}")
        print(f"{'-'*70}")
        
        result = chatbot.chat_detailed(query)
        print(f"🤖 Bot:\n{result['answer']}")
        print(f"\n📊 Confidence: {result['confidence']} | Sources: {result['num_sources']}")
    
    print(f"\n{'='*70}")
    print("✅ Test completed!")
    

if __name__ == "__main__":
    test_chatbot()

