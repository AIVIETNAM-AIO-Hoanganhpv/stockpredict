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

echo Dang cai thu vien (lan dau mat vai phut)...
%PY% -m pip install -q -r requirements.txt || (
    echo Cai thu vien that bai. Kiem tra ket noi mang roi chay lai.
    pause
    exit /b 1
)

echo.
echo Web app se mo trong trinh duyet. Dien thoai cung mang Wi-Fi: mo dia chi "Network URL" hien ben duoi.
echo Dong cua so nay de tat web app.
%PY% -m streamlit run web_app.py --server.address 0.0.0.0 --browser.gatherUsageStats false
pause
