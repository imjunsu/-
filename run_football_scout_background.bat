@echo off
cd /d "%~dp0"
"C:\Users\user\AppData\Local\Programs\Python\Python312\python.exe" -m streamlit run app.py --server.port 8501 --server.headless true > streamlit.hidden.log 2>&1
