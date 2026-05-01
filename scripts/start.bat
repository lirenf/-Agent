@echo off
chcp 65001 >nul
echo.
echo ╔══════════════════════════════════════════╗
echo ║     PaperMind — 论文深度分析 Agent      ║
echo ╚══════════════════════════════════════════╝
echo.

:: 加载 .env
if exist "%~dp0..\.env" (
  for /f "tokens=1,2 delims==" %%a in (%~dp0..\.env) do (
    if not "%%a"=="" if not "%%a:~0,1%"=="#" set %%a=%%b
  )
)

if "%ANTHROPIC_API_KEY%"=="" (
  echo ❌ 未设置 ANTHROPIC_API_KEY
  echo 请在项目根目录创建 .env 文件并填入 API Key
  pause
  exit /b 1
)

cd /d "%~dp0..\backend"
echo 📦 安装依赖...
pip install -r requirements.txt -q

echo.
echo 🚀 启动服务: http://localhost:8000
echo.

python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
pause
