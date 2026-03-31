@"
@echo off
cd /d "G:\System Architecture – JobPulse Data Pipeline"
"G:\System Architecture – JobPulse Data Pipeline\.venv\Scripts\python.exe" "G:\System Architecture – JobPulse Data Pipeline\scheduler\run_pipeline.py"
"@ | Out-File -FilePath "G:\System Architecture – JobPulse Data Pipeline\scheduler\run_pipeline.bat" -Encoding ASCII