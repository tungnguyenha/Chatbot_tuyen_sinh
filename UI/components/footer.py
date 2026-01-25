import streamlit as st

def render_footer(university_name):
    st.markdown(f"""
    <div class="footer">
        <p>
            💡 <b>Tip:</b> Hãy hỏi càng cụ thể càng tốt để nhận câu trả lời chính xác nhất!<br>
        </p>
    </div>
    """, unsafe_allow_html=True)