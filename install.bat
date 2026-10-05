@echo off
setlocal
chcp 65001 >nul
title pptx_maker 설치
echo ==========================================
echo   pptx_maker 연결 (Windows)
echo ==========================================
set "PY="
for %%C in ("py -3" "python" "python3") do (
  if not defined PY (
    %%~C -c "import sys; raise SystemExit(0 if sys.version_info >= (3,9) else 1)" >nul 2>nul && set "PY=%%~C"
  )
)
if not defined PY (
  echo [!] 파이썬 3.9 이상이 필요합니다: winget install -e --id Python.Python.3.12
  pause
  exit /b 1
)
set "PYTHONPATH=%~dp0"
%PY% -c "import PIL" >nul 2>nul || (
  echo [선택] 사진 자르기·압축과 모아 보기에 Pillow 가 쓰입니다.
  set /p ANS="지금 설치할까요? [Y/n] "
  if /i not "%ANS%"=="n" %PY% -m pip install --user pillow
)
%PY% -m pptx_maker doctor
echo.
%PY% -m pptx_maker setup
echo.
echo 끝났습니다. AI 프로그램(Claude Code 등)을 다시 시작하면 pptx_maker 도구와 스킬이 보입니다.
pause
