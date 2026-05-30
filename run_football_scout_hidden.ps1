$ProjectDir = $PSScriptRoot
$Python = "C:\Users\user\AppData\Local\Programs\Python\Python312\python.exe"
$Arguments = @(
    "-m",
    "streamlit",
    "run",
    "app.py",
    "--server.port",
    "8501",
    "--server.headless",
    "true"
)
$OutLog = Join-Path $ProjectDir "streamlit.hidden.out.log"
$ErrLog = Join-Path $ProjectDir "streamlit.hidden.err.log"
Start-Process -FilePath $Python -ArgumentList $Arguments -WorkingDirectory $ProjectDir -WindowStyle Hidden -RedirectStandardOutput $OutLog -RedirectStandardError $ErrLog
