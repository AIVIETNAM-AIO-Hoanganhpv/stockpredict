"""Xuất kết quả: báo cáo HTML có biểu đồ, bảng tóm tắt Markdown và Excel, chữ trên màn hình."""
import datetime as dt
import html
import re
from pathlib import Path

import pandas as pd

from . import chi_bao
from .phan_tich import KetQua

MAU = {1: "#16a34a", -1: "#dc2626", 0: "#64748b"}
MUI_TEN = {1: "▲", -1: "▼", 0: "■"}
CANH_BAO = ("Công cụ chỉ hỗ trợ phân tích kỹ thuật, không phải lời khuyên đầu tư. "
            "Không có phương pháp nào dự đoán đúng 100%.")


def _f(x):
    if x is None or x != x:
        return "–"
    if abs(x) >= 1000:
        return f"{x:,.0f}"
    return f"{x:,.2f}" if abs(x) >= 10 else f"{x:,.5f}".rstrip("0").rstrip(".")


def ten_file(ma: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "_", ma) + ".html"


def ke_hoach(kq: KetQua) -> dict:
    if not kq.khung:
        return {}
    p = kq.chinh.fibo
    if not p or not kq.xu_huong or (p.up != (kq.xu_huong > 0)):
        return {}
    if kq.loai in ("vn", "intl") and kq.xu_huong < 0:
        return {}          # cổ phiếu không bán khống được → không đưa kế hoạch bán
    return {"vao": kq.chinh.gia, "sl": p.sl, "tp1": p.tp1, "tp2": p.tp2, "hoi": p.depth}


# ---------------------------------------------------------------------------- văn bản
def van_ban(kq: KetQua, chi_tiet: bool = True) -> str:
    dong = [f"{kq.ma}: {MUI_TEN[kq.xu_huong]} {kq.nhan.upper()}  "
            f"(điểm {kq.diem:+.0f}/100, đồng thuận {kq.dong_thuan})"]
    for k in kq.khung:
        dong.append(f"  [{k.khung:>3}] {k.nhan:<9} điểm {k.diem:+6.1f}   giá {_f(k.gia)}")
        if chi_tiet:
            for v in k.votes:
                dong.append(f"         {MUI_TEN[(v.gia_tri > 0) - (v.gia_tri < 0)]} {v.ten}: {v.ly_do}")
            for g in k.ghi_chu:
                dong.append(f"         • {g}")
    kh = ke_hoach(kq)
    if kh:
        dong.append(f"  Kế hoạch (Fibonacci, khung {kq.chinh.khung}): vào ~{_f(kh['vao'])}, "
                    f"cắt lỗ {_f(kh['sl'])}, chốt lời {_f(kh['tp1'])}"
                    + (f" / {_f(kh['tp2'])}" if kh["tp2"] else "") + f" (hồi {kh['hoi']:.0%})")
    for g in kq.ghi_chu:
        dong.append(f"  ! {g}")
    return "\n".join(dong)


# ---------------------------------------------------------------------------- biểu đồ
def bieu_do(df: pd.DataFrame, kq_khung, ten: str):
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    full, df = df, df.iloc[-200:]
    st, plan = kq_khung.cau_truc, kq_khung.fibo
    fig = make_subplots(rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.025,
                        row_heights=[0.55, 0.15, 0.15, 0.15],
                        subplot_titles=(f"{ten} – khung {kq_khung.khung}", "MACD",
                                        "Stochastic & MFI", "ADX"))
    fig.add_trace(go.Candlestick(x=df.index, open=df["open"], high=df["high"], low=df["low"],
                                 close=df["close"], name="Giá"), 1, 1)
    fig.add_trace(go.Scatter(x=df.index, y=chi_bao.sma(full["close"], 20).iloc[-len(df):], name="MA20",
                             line=dict(width=1, color="#f59e0b")), 1, 1)

    for z in (st.order_blocks + st.fvgs) if st else []:
        color = "rgba(22,163,74,0.18)" if z.side > 0 else "rgba(220,38,38,0.18)"
        x0 = max(full.index[min(z.i, len(full) - 1)], df.index[0])
        fig.add_shape(type="rect", xref="x", yref="y", x0=x0, x1=df.index[-1],
                      y0=z.bottom, y1=z.top, fillcolor=color, line_width=0, row=1, col=1)
        fig.add_annotation(x=df.index[-1], y=z.top, text=f"{z.kind}", showarrow=False,
                           font=dict(size=9), xanchor="left", row=1, col=1)
    if plan:
        for r, y in plan.retrace.items():
            fig.add_hline(y=y, line=dict(color="#6366f1", width=1, dash="dot"),
                          annotation_text=f"Fibo {r:g}", annotation_font_size=9, row=1, col=1)
        for lbl, y, col in (("TP1", plan.tp1, "#16a34a"), ("TP2", plan.tp2, "#16a34a"),
                            ("SL", plan.sl, "#dc2626")):
            if y:
                fig.add_hline(y=y, line=dict(color=col, width=1.5),
                              annotation_text=lbl, annotation_font_size=10, row=1, col=1)

    m = chi_bao.macd(full).iloc[-len(df):]
    fig.add_trace(go.Bar(x=df.index, y=m["hist"], name="Histogram",
                         marker_color=["#16a34a" if v >= 0 else "#dc2626" for v in m["hist"]]), 2, 1)
    fig.add_trace(go.Scatter(x=df.index, y=m["macd"], name="MACD", line=dict(width=1)), 2, 1)
    fig.add_trace(go.Scatter(x=df.index, y=m["signal"], name="Tín hiệu", line=dict(width=1)), 2, 1)

    s = chi_bao.stoch(full).iloc[-len(df):]
    fig.add_trace(go.Scatter(x=df.index, y=s["k"], name="%K", line=dict(width=1)), 3, 1)
    fig.add_trace(go.Scatter(x=df.index, y=s["d"], name="%D", line=dict(width=1)), 3, 1)
    if df["volume"].sum() > 0:
        fig.add_trace(go.Scatter(x=df.index, y=chi_bao.mfi(full).iloc[-len(df):], name="MFI",
                                 line=dict(width=1, dash="dot")), 3, 1)
    for y in (20, 80):
        fig.add_hline(y=y, line=dict(color="#94a3b8", width=1, dash="dash"), row=3, col=1)

    a = chi_bao.adx(full).iloc[-len(df):]
    fig.add_trace(go.Scatter(x=df.index, y=a["adx"], name="ADX", line=dict(width=1.5)), 4, 1)
    fig.add_trace(go.Scatter(x=df.index, y=a["pdi"], name="+DI", line=dict(width=1)), 4, 1)
    fig.add_trace(go.Scatter(x=df.index, y=a["mdi"], name="-DI", line=dict(width=1)), 4, 1)
    fig.add_hline(y=25, line=dict(color="#94a3b8", width=1, dash="dash"), row=4, col=1)

    if kq_khung.khung not in ("W", "M"):
        fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])   # bỏ khoảng trống cuối tuần
    fig.update_layout(height=900, template="plotly_white", xaxis_rangeslider_visible=False,
                      margin=dict(l=40, r=60, t=40, b=20), legend=dict(orientation="h", y=-0.03))
    return fig



# ---------------------------------------------------------------------------- HTML
CSS = """
body{font-family:Segoe UI,Arial,sans-serif;margin:0;background:#f8fafc;color:#0f172a}
main{max-width:1200px;margin:auto;padding:24px}
.cuon{overflow-x:auto;-webkit-overflow-scrolling:touch}
@media (max-width:640px){main{padding:12px}h1{font-size:22px}th,td{padding:6px;font-size:13px}}
h1{margin:0 0 4px} .muted{color:#64748b;font-size:13px}
table{border-collapse:collapse;width:100%;background:#fff;margin:12px 0;font-size:14px}
th,td{padding:8px 10px;border-bottom:1px solid #e2e8f0;text-align:left;vertical-align:top}
th{background:#f1f5f9} .tag{font-weight:600;padding:2px 8px;border-radius:10px;color:#fff}
.card{background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:16px;margin:12px 0}
a{color:#2563eb;text-decoration:none}
"""


def _tag(xh, text):
    return f'<span class="tag" style="background:{MAU[xh]}">{MUI_TEN[xh]} {html.escape(text)}</span>'


def _trang(title, body):
    return (f"<!DOCTYPE html><html lang='vi'><head><meta charset='utf-8'>"
            f"<meta name='viewport' content='width=device-width,initial-scale=1'>"
            f"<title>{html.escape(title)}</title><style>{CSS}</style></head>"
            f"<body><main>{body}<p class='muted'>{CANH_BAO}</p></main></body></html>")


def html_ma(kq: KetQua, df_chinh: pd.DataFrame | None, thoi_gian: str, thu_lai: dict | None) -> str:
    kh = ke_hoach(kq)
    body = ["<p><a href='index.html'>← Tất cả mã</a></p>",
            f"<h1>{html.escape(kq.ma)} {_tag(kq.xu_huong, kq.nhan)}</h1>",
            f"<p class='muted'>Cập nhật {thoi_gian} · điểm {kq.diem:+.0f}/100 · "
            f"đồng thuận {kq.dong_thuan}</p>"]
    if kh:
        body.append("<div class='card'><b>Kế hoạch theo Fibonacci</b> (khung "
                    f"{kq.chinh.khung}): vào quanh <b>{_f(kh['vao'])}</b> · cắt lỗ <b>{_f(kh['sl'])}</b>"
                    f" · chốt lời <b>{_f(kh['tp1'])}</b>"
                    + (f" / {_f(kh['tp2'])}" if kh["tp2"] else "")
                    + f" · giá đã hồi {kh['hoi']:.0%} nhịp trước</div>")
    if thu_lai and thu_lai.get("ti_le") is not None:
        body.append(f"<div class='card'>Thử lại trên quá khứ (khung {kq.chinh.khung}): "
                    f"{thu_lai['dung']}/{thu_lai['tin_hieu']} tín hiệu đúng chiều sau "
                    f"{thu_lai['toi']} nến = <b>{thu_lai['ti_le']:.0%}</b></div>")
    for g in kq.ghi_chu:
        body.append(f"<div class='card'>⚠ {html.escape(g)}</div>")
    body.append("<div class='cuon'><table><tr><th>Khung</th><th>Xu hướng</th><th>Điểm</th><th>Giá</th>"
                "<th>Chi tiết</th></tr>")
    for k in kq.khung:
        det = "<br>".join(f"{MUI_TEN[(v.gia_tri > 0) - (v.gia_tri < 0)]} <b>{html.escape(v.ten)}</b>: "
                          f"{html.escape(v.ly_do)}" for v in k.votes)
        det += "".join(f"<br>• <i>{html.escape(g)}</i>" for g in k.ghi_chu)
        body.append(f"<tr><td>{k.khung}</td><td>{_tag(k.xu_huong, k.nhan)}</td>"
                    f"<td>{k.diem:+.1f}</td><td>{_f(k.gia)}</td><td>{det}</td></tr>")
    body.append("</table></div>")
    if df_chinh is not None and len(df_chinh) > 30:
        fig = bieu_do(df_chinh, kq.chinh, kq.ma)
        body.append(fig.to_html(full_html=False, include_plotlyjs="cdn"))
    return _trang(f"{kq.ma} – {kq.nhan}", "".join(body))


def html_index(ds: list[KetQua], thoi_gian: str) -> str:
    rows = []
    for kq in ds:
        kh = ke_hoach(kq)
        khung = " ".join(f"<span style='color:{MAU[k.xu_huong]}'>{k.khung}{MUI_TEN[k.xu_huong]}</span>"
                         for k in kq.khung)
        rows.append(f"<tr><td><a href='{ten_file(kq.ma)}'><b>{html.escape(kq.ma)}</b></a></td>"
                    f"<td>{_tag(kq.xu_huong, kq.nhan)}</td><td>{kq.diem:+.0f}</td>"
                    f"<td>{khung}</td><td>{_f(kq.chinh.gia) if kq.khung else '–'}</td>"
                    f"<td>{_f(kh.get('sl'))}</td><td>{_f(kh.get('tp1'))}</td></tr>")
    body = (f"<h1>Dự đoán xu hướng</h1><p class='muted'>Cập nhật {thoi_gian}. "
            "Stoch · MACD · MFI · ADX · ICT · SMC · Fibonacci · LEVEL 1</p>"
            "<div class='cuon'><table><tr><th>Mã</th><th>Dự đoán</th><th>Điểm</th><th>Các khung</th><th>Giá</th>"
            "<th>Cắt lỗ</th><th>Chốt lời</th></tr>" + "".join(rows) + "</table></div>")
    return _trang("Dự đoán xu hướng", body)


# ---------------------------------------------------------------------------- bảng
def bang(ds: list[KetQua]) -> pd.DataFrame:
    rows = []
    for kq in ds:
        kh = ke_hoach(kq)
        row = {"Mã": kq.ma, "Dự đoán": kq.nhan, "Điểm": kq.diem, "Đồng thuận": kq.dong_thuan,
               "Giá": kq.chinh.gia if kq.khung else None,
               "Cắt lỗ": kh.get("sl"), "Chốt lời 1": kh.get("tp1"), "Chốt lời 2": kh.get("tp2")}
        for k in kq.khung:
            row[f"Khung {k.khung}"] = f"{k.nhan} ({k.diem:+.0f})"
        row["Ghi chú"] = " ".join(kq.ghi_chu)
        rows.append(row)
    return pd.DataFrame(rows)


def markdown(ds: list[KetQua], thoi_gian: str) -> str:
    out = [f"# Dự đoán xu hướng – {thoi_gian}", "",
           "| Mã | Dự đoán | Điểm | Các khung | Giá | Cắt lỗ | Chốt lời |",
           "|---|---|---:|---|---:|---:|---:|"]
    for kq in ds:
        kh = ke_hoach(kq)
        khung = " ".join(f"{k.khung}{MUI_TEN[k.xu_huong]}" for k in kq.khung)
        out.append(f"| [{kq.ma}]({ten_file(kq.ma)}) | {MUI_TEN[kq.xu_huong]} {kq.nhan} | {kq.diem:+.0f} | "
                   f"{khung} | {_f(kq.chinh.gia) if kq.khung else '–'} | {_f(kh.get('sl'))} | "
                   f"{_f(kh.get('tp1'))} |")
    out += ["", f"> {CANH_BAO}", ""]
    return "\n".join(out)


def ghi(thu_muc, ds: list[KetQua], du_lieu: dict, thu_lai: dict | None = None) -> Path:
    """Ghi toàn bộ báo cáo vào thư mục. `du_lieu`: {mã: DataFrame khung chính}."""
    thu_muc = Path(thu_muc)
    thu_muc.mkdir(parents=True, exist_ok=True)
    thoi_gian = dt.datetime.now(dt.timezone(dt.timedelta(hours=7))).strftime("%d/%m/%Y %H:%M (GMT+7)")
    thu_lai = thu_lai or {}
    for kq in ds:
        (thu_muc / ten_file(kq.ma)).write_text(
            html_ma(kq, du_lieu.get(kq.ma), thoi_gian, thu_lai.get(kq.ma)), encoding="utf-8")
    (thu_muc / "index.html").write_text(html_index(ds, thoi_gian), encoding="utf-8")
    (thu_muc / "README.md").write_text(markdown(ds, thoi_gian), encoding="utf-8")
    bang(ds).to_excel(thu_muc / "tom_tat.xlsx", index=False)
    return thu_muc / "index.html"
