Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
WshShell.Run "cmd /c streamlit run app_streamlit.py --server.headless true", 1, False
WScript.Sleep 3000
WshShell.Run "http://localhost:8501"


