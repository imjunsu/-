Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
projectDir = fso.GetParentFolderName(WScript.ScriptFullName)
shell.CurrentDirectory = projectDir
command = """" & fso.BuildPath(projectDir, "run_football_scout_background.bat") & """"
shell.Run command, 0, False
