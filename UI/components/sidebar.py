import streamlit as st

def render_sidebar(example_questions,hotline,email,website):
    st.header("ℹ️ Thông tin hệ thống")

    st.markdown("""
    <div class="sidebar-info">
            <b>📚 Tôi có thể giúp bạn:</b><br>
            • Thông tin các ngành học<br>
            • Điểm chuẩn các năm<br>
            • Học phí và học bổng<br>
            • Phương thức xét tuyển<br>
            • Câu hỏi thường gặp<br>
        </div>
    """,unsafe_allow_html=True)

    st.markdown("💡 Ví dụ câu hỏi:")
    for q in example_questions:
        if st.button(q,key=f"example_{q}",use_container_width=True):
            st.session_state.example_query = q

    st.divider()
    st.markdown("⚙️ Cài đặt:")
    st.session_state.show_sources = st.toggle(
        "Hiển thị nguồn tham khảo",
        value=st.session_state.show_sources)

    st.divider()

    st.markdown(f"""
        <div class="sidebar-info">
            <b>📞 Liên hệ:</b><br>
            Hotline: {hotline}<br>
            Email: {email}<br>
            Website: <a href="{website}" target="_blank">Link</a>
        </div>
        """, unsafe_allow_html=True)
    
    if st.button("🔄 Bắt đầu cuộc trò chuyện mới", type="primary", use_container_width=True):
        st.session_state.messages = []
        st.session_state.total_queries = 0
        st.rerun()

    st.divider()
    col1,col2 = st.columns(2)
    col1.metric("Số câu hỏi", st.session_state.total_queries)
    col1.metric("Tin nhắn", len(st.session_state.messages))