@echo off
chcp 65001 >nul
cd /d "%~dp0"

set PY=py
where py >nul 2>nul || set PY=python
where %PY% >nul 2>nul || (
    echo Khong tim thay Python. Hay cai Python tu https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Dang cai thu vien (lan dau mat khoang 1-2 phut)...
%PY% -m pip install -q -r requirements.txt || (
    echo Cai thu vien that bai. Kiem tra ket noi mang roi chay lai.
    pause
    exit /b 1
)
%PY% -m pip install -q vnstock >nul 2>nul

:hoi
echo.
echo Nhap ma can phan tich, cach nhau boi dau cach (VD: FPT EURUSD XAUUSD).
echo Bo trong roi Enter = phan tich tat ca ma trong ma.txt va mo bao cao.
set "MA="
set /p MA="Ma: "
if "%MA%"=="" (
    %PY% du_doan.py --tat-ca --bao-cao --gon
    start "" "bao_cao\index.html"
) else (
    %PY% du_doan.py %MA% --thu-lai
)
goto hoi
