"""Web app dự đoán xu hướng – mở được trên điện thoại.

Chạy trên máy:      py -m streamlit run web_app.py   (hoặc bấm run_web.bat)
Đưa lên mạng:       Streamlit Community Cloud, file chính co_phieu/web_app.py
"""
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from dudoan import bao_cao, du_lieu  # noqa: E402
from du_doan import phan_tich_ma  # noqa: E402

st.set_page_config(page_title="Dự đoán xu hướng", page_icon="📈", layout="centered")

MAU = {1: "#16a34a", -1: "#dc2626", 0: "#64748b"}
MUI_TEN = bao_cao.MUI_TEN
_f = bao_cao._f


@st.cache_data(ttl=300, show_spinner=False)
def phan_tich(ma: str, thu_lai: bool):
    """Kết quả được dùng lại trong 5 phút để tải trang nhanh hơn."""
    return phan_tich_ma(ma, thu_lai=thu_lai)


@st.cache_data(ttl=3600, show_spinner=False)
def phan_tich_danh_sach(ds: tuple):
    """Cả danh sách theo dõi: tự làm mới mỗi giờ."""
    out = []
    for ma in ds:
        try:
            out.append(phan_tich_ma(ma)[0])
        except Exception as e:  # một mã lỗi không làm hỏng cả bảng
            st.warning(f"{ma}: {e}")
    return out, pd.Timestamp.now(tz="Asia/Ho_Chi_Minh").strftime("%H:%M %d/%m/%Y")


def the_ket_qua(kq):
    mau = MAU[kq.xu_huong] if kq.khung else "#64748b"
    st.markdown(
        f"<div style='padding:14px 16px;border-radius:12px;background:{mau};color:white'>"
        f"<div style='font-size:15px;opacity:.9'>{kq.ma}</div>"
        f"<div style='font-size:30px;font-weight:700'>{MUI_TEN[kq.xu_huong]} {kq.nhan}</div>"
        f"<div style='font-size:14px'>Điểm {kq.diem:+.0f}/100 · đồng thuận {kq.dong_thuan}</div></div>",
        unsafe_allow_html=True)


def chi_tiet(kq, tl, tab: str):
    the_ket_qua(kq)
    if not kq.khung:
        for g in kq.ghi_chu:
            st.error(g)
        return
    kh = bao_cao.ke_hoach(kq)
    c1, c2, c3 = st.columns(3)
    c1.metric("Giá", _f(kq.chinh.gia))
    c2.metric("Cắt lỗ", _f(kh.get("sl")))
    c3.metric("Chốt lời", _f(kh.get("tp1")))
    if kh:
        st.caption(f"Kế hoạch Fibonacci khung {kq.chinh.khung}: giá đã hồi {kh['hoi']:.0%} nhịp trước"
                   + (f" · chốt lời 2: {_f(kh['tp2'])}" if kh.get("tp2") else ""))
    else:
        st.caption("Chưa có kế hoạch vào lệnh (xu hướng đi ngang hoặc chưa rõ).")
    if tl and tl.get("ti_le") is not None:
        st.info(f"Thử lại trên quá khứ (khung {kq.chinh.khung}): {tl['dung']}/{tl['tin_hieu']} tín hiệu "
                f"đúng chiều sau {tl['toi']} nến = **{tl['ti_le']:.0%}**")
    for g in kq.ghi_chu:
        st.warning(g)

    st.markdown("##### Các khung thời gian")
    for k in kq.khung:
        with st.expander(f"{MUI_TEN[k.xu_huong]} Khung {k.khung}: {k.nhan} ({k.diem:+.0f})"):
            for v in k.votes:
                dau = MUI_TEN[(v.gia_tri > 0) - (v.gia_tri < 0)]
                st.markdown(f"{dau} **{v.ten}**: {v.ly_do}")
            for g in k.ghi_chu:
                st.caption("• " + g)

    st.markdown("##### Biểu đồ")
    ten_khung = [k.khung for k in kq.khung]
    chon = st.radio("Khung", ten_khung, index=ten_khung.index(kq.chinh.khung), horizontal=True,
                    key=f"khung_{tab}_{kq.ma}", label_visibility="collapsed")
    kk = next(k for k in kq.khung if k.khung == chon)
    df = kq.frames.get(chon)
    if df is not None and len(df) > 30:
        fig = bao_cao.bieu_do(df, kk, kq.ma)
        fig.update_layout(height=760, margin=dict(l=8, r=8, t=36, b=8), showlegend=False,
                          dragmode="pan")
        st.plotly_chart(fig, width="stretch", config={"scrollZoom": True, "displaylogo": False})


# ------------------------------------------------------------------------------------------
st.markdown("## 📈 Dự đoán xu hướng")
st.caption("Stoch · MACD · MFI · ADX · ICT · SMC · Fibonacci · LEVEL 1")

tab1, tab2 = st.tabs(["🔍 Tra cứu", "📋 Danh sách theo dõi"])
mac_dinh = du_lieu.doc_danh_sach(HERE / "ma.txt")

with tab1:
    with st.form("tra_cuu"):
        ma = st.text_input("Mã (VD: FPT, EURUSD, XAUUSD, AAPL)", value=st.session_state.get("ma", "FPT"))
        thu_lai = st.checkbox("Thử lại trên quá khứ (chậm hơn)", value=True)
        ok = st.form_submit_button("Phân tích", type="primary", width="stretch")
    if ok:
        st.session_state["ma"] = ma.strip().upper()
    ma = st.session_state.get("ma", "FPT")
    if ma:
        with st.spinner(f"Đang phân tích {ma}…"):
            kq, _, tl = phan_tich(ma, thu_lai)
        chi_tiet(kq, tl, "tra_cuu")

with tab2:
    ds_txt = st.text_area("Danh sách mã (cách nhau bởi dấu cách hoặc xuống dòng)",
                          value=" ".join(mac_dinh), height=80)
    ds = tuple(x for x in ds_txt.replace(",", " ").split() if x)
    if st.button("🔄 Làm mới ngay", width="stretch"):
        phan_tich_danh_sach.clear()
    with st.spinner("Đang phân tích danh sách…"):
        ket_qua, luc = phan_tich_danh_sach(ds)
    st.caption(f"Cập nhật lúc {luc} (tự làm mới mỗi giờ)")
    bang = pd.DataFrame([{
        "Mã": k.ma,
        "Dự đoán": f"{MUI_TEN[k.xu_huong]} {k.nhan}",
        "Điểm": round(k.diem),
        "Giá": _f(k.chinh.gia) if k.khung else "–",
        "Cắt lỗ": _f(bao_cao.ke_hoach(k).get("sl")),
        "Chốt lời": _f(bao_cao.ke_hoach(k).get("tp1")),
        "Khung": " ".join(f"{x.khung}{MUI_TEN[x.xu_huong]}" for x in k.khung),
    } for k in ket_qua])
    if not bang.empty:
        def to_mau(v):
            return ("color:#16a34a;font-weight:600" if "▲" in str(v) else
                    "color:#dc2626;font-weight:600" if "▼" in str(v) else "")
        st.dataframe(bang.style.map(to_mau, subset=["Dự đoán"]), hide_index=True,
                     width="stretch")
        chon = st.selectbox("Xem chi tiết mã", [k.ma for k in ket_qua])
        kq = next(k for k in ket_qua if k.ma == chon)
        chi_tiet(kq, None, "danh_sach")

st.divider()
st.caption("⚠ " + bao_cao.CANH_BAO)
