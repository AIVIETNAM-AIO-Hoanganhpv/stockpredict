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

%PY% -c "import pandas, numpy" >nul 2>nul && goto chay
echo Dang cai thu vien - lan dau mat vai phut...
%PY% -m pip install --disable-pip-version-check --no-warn-script-location -r requirements.txt || (
    echo Cai thu vien that bai. Kiem tra mang roi chay lai, hoac chup man hinh gui lai.
    pause
    exit /b 1
)

:chay
echo Dang mo GreenView voi gia co phieu Viet Nam... Trinh duyet se tu mo.
echo Dong cua so nay de tat.
%PY% chay_greenview.py
pause
