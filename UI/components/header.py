import streamlit as st

def render_header(page_icon, university_name):
    st.markdown(f"""
         <div class="main-header">       
        <h1>{page_icon} Trợ lý tư vấn tuyển sinh<h1>
        <p>{university_name}- Hệ thống tư vấn tuyển sinh thông minh được hổ trở bởi AI<p>
                <div>
        """,unsafe_allow_html=True)