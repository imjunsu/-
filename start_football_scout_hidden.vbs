Set shell = CreateObject("WScript.Shell")
shell.CurrentDirectory = "C:\Users\Public\Documents\ESTsoft\CreatorTemp\football_scout"
shell.Run "cmd /c run_football_scout_background.bat", 0, False
