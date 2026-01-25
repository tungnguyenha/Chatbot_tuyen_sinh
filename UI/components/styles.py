import streamlit as st

def inject_css():
    st.markdown("""
    <style>
        /* Main header */
        .main-header {
            text-align: center;
            padding: 2rem 1rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 15px;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }

        .main-header h1 {
            margin: 0;
            font-size: 2.5rem;
            font-weight: 700;
        }

        .main-header p {
            margin: 0.5rem 0 0 0;
            font-size: 1.1rem;
            opacity: 0.9;
        }

        .sidebar-info {
            background-color: #02020A;
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 1rem;
        }

        .source-box {
            background-color: #f8f9fa;
            border-left: 3px solid #667eea;
            padding: 0.75rem;
            margin: 0.5rem 0;
            border-radius: 5px;
        }

        .footer {
            text-align: center;
            padding: 2rem;
            color: #666;
            margin-top: 3rem;
            border-top: 1px solid #ddd;
        }
    </style>
    """, unsafe_allow_html=True)

    