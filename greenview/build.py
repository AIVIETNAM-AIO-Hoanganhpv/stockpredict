"""
build.py — Gộp toàn bộ mã nguồn trong src/ thành MỘT file HTML (dist/GreenView.html)
để mở trực tiếp bằng trình duyệt, không cần cài gì.   Cách chạy:  python build.py
"""
import re
from pathlib import Path

SRC = Path(__file__).parent / "src"
OUT = Path(__file__).parent / "dist" / "GreenView.html"

html = (SRC / "index.html").read_text(encoding="utf-8")
css = (SRC / "css" / "app.css").read_text(encoding="utf-8")
html = html.replace('<link rel="stylesheet" href="css/app.css">', "<style>\n" + css + "\n</style>")

def inline(m):
    code = (SRC / m.group(1)).read_text(encoding="utf-8").replace("</script", "<\\/script")
    return "<script>\n/* --- " + m.group(1) + " --- */\n" + code + "\n</script>"

html = re.sub(r'<script src="([^"]+)"></script>', inline, html)
OUT.parent.mkdir(exist_ok=True)
OUT.write_text(html, encoding="utf-8")
print("Đã tạo", OUT, f"({OUT.stat().st_size // 1024} KB)")
