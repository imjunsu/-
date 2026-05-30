$ProjectDir = $PSScriptRoot
Set-Location -LiteralPath $ProjectDir
$LogPath = Join-Path $ProjectDir "streamlit.run.log"
& "C:\Users\user\AppData\Local\Programs\Python\Python312\python.exe" -m streamlit run app.py --server.port 8501 --server.headless true *> $LogPath
