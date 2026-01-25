import streamlit as st
from src.utils import truncate_text


def render_Chat_history():
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            if(
                message["role"] == "assistant"
                and "sources" in message
                and st.session_state.show_sources
                and message["sources"]
            ):
                with st.expander("📚 Xem nguồn tham khảo"):
                    for i,source in enumerate(message["source"],1):
                        st.markdown(f"""
                        <div class="source-box">
                            <b>Nguồn {i}:</b> {source.metadata.get('type', 'unknown')}<br>
                            {truncate_text(source.page_content, 150)}
                        </div>
                        """, unsafe_allow_html=True)

def handle_chat_input(chatbot):
    prompt = None
    if "example_query" in st.session_state:
        prompt = st.session_state.example_query
        del st.session_state.example_query
    else:
        prompt = st.chat_input("Nhập câu hỏi của bạn...")
    
    if not prompt:
        return
    
    st.session_state.messages.append({"role":"user", "content":prompt})
    st.session_state.total_queries += 1

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("⏳ Đang suy nghĩ..."):
            result = chatbot.chat_detailed(prompt)
            response = result["answer"]

            st.markdown(response)

            col1, col2, col3 = st.columns(3)
            col1.caption(f"📊 Độ tin cậy: {result['confidence']}")
            col2.caption(f"🔍 Loại: {result['query_type']}")
            col3.caption(f"📚 Nguồn: {result['num_sources']}")

            if st.session_state.show_sources and result["sources"]:
                with st.expander("📚 Xem nguồn tham khảo"):
                    for i, source in enumerate(result["sources"], 1):
                        st.markdown(f"""
                        <div class="source-box">
                            <b>Nguồn {i}:</b> {source.metadata.get('type', 'unknown')}<br>
                            {truncate_text(source.page_content, 150)}
                        </div>
                        """, unsafe_allow_html=True)

            st.session_state.messages.append({
                "role": "assistant",
                "content": response,
                "sources": result["sources"]
            })

