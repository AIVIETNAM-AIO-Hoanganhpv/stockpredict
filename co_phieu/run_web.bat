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

rem Da cai du thu vien roi thi bo qua buoc cai (mo app nhanh hon)
%PY% -c "import streamlit, pandas, plotly, yfinance, openpyxl" >nul 2>nul && goto chay

echo [1/2] Dang cai thu vien - lan dau mat 3-10 phut tuy mang. Dung tat cua so nay...
%PY% -m pip install --disable-pip-version-check --no-warn-script-location -r requirements.txt || (
    echo.
    echo Cai thu vien that bai. Kiem tra ket noi mang roi chay lai.
    echo Neu van loi: chup man hinh cua so nay gui lai.
    pause
    exit /b 1
)

:chay
echo.
echo [2/2] Dang mo web app... Trinh duyet se tu mo dia chi http://localhost:8501
echo Dien thoai cung mang Wi-Fi: mo dia chi "Network URL" hien ben duoi.
echo Dong cua so nay de tat web app.
echo.
%PY% -m streamlit run web_app.py --server.address 0.0.0.0 --browser.gatherUsageStats false --server.headless false
echo.
echo Web app da dung. Neu co loi o tren, chup man hinh gui lai.
pause
