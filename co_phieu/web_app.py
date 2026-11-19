"""Web app dự đoán xu hướng – mở được trên điện thoại.

Chạy trên máy:      py -m streamlit run web_app.py   (hoặc bấm run_web.bat)
Đưa lên mạng:       Streamlit Community Cloud, file chính co_phieu/web_app.py
"""
import json
import sys
import time
from pathlib import Path

import pandas as pd
import streamlit as st

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from dudoan import bao_cao, co_ban as CB, du_lieu, khuyen_nghi as K, quet, tin_tuc as TT  # noqa: E402
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
        st.plotly_chart(fig, width="stretch", config={"scrollZoom": True, "displaylogo": False},
                        key=f"bieu_do_{tab}_{kq.ma}_{chon}")


# ------------------------------------------------------------------------------------------ khuyến nghị
TAM = {"Ngắn hạn – khung ngày (1–3 tháng)": "D", "Trung hạn – khung tuần (3–9 tháng)": "W"}
FILE_TT = HERE / "bao_cao" / "thi_truong.json"
FILE_DM = HERE / "danh_muc.csv"


def tien(x):
    return "–" if x is None or pd.isna(x) else f"{x:,.0f} đ"


def the_khuyen_nghi(kn, von: float, lo: int = 100):
    """Thẻ khuyến nghị + máy tính lãi/lỗ theo số vốn."""
    mau = K.MAU_MUC.get(kn.muc, "#64748b")
    st.markdown(
        f"<div style='padding:12px 16px;border-radius:12px;border:2px solid {mau}'>"
        f"<div style='font-size:13px;color:#64748b'>Khuyến nghị {'ngắn hạn (D)' if kn.tam == 'D' else 'trung hạn (W)'}</div>"
        f"<div style='font-size:26px;font-weight:700;color:{mau}'>{kn.muc}</div>"
        + (f"<div style='font-size:15px'>Vùng mua đẹp: <b>{kn.vung.thap:,.0f} – {kn.vung.cao:,.0f}</b></div>"
           if kn.vung else "") + "</div>", unsafe_allow_html=True)
    if kn.gia_mua:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Giá mua", _f(kn.gia_mua),
                  f"{-kn.cach_vung_pct:+.1%} so với giá" if kn.cach_vung_pct else "mua ngay",
                  delta_color="off")
        c2.metric("Cắt lỗ", _f(kn.cat_lo), f"{kn.lo_pct:+.1%}" if kn.lo_pct is not None else None)
        c3.metric("Chốt lời", _f(kn.chot_loi1), f"{kn.lai_pct:+.1%}" if kn.lai_pct is not None else None)
        c4.metric("Lãi/Lỗ (R:R)", f"{kn.rr:.1f}" if kn.rr else "–")
        lai = K.ke_hoach_von(kn, von, lo)
        if lai.get("tp1") and lai["tp1"]["so_cp"] > 0:
            rows = [("Chốt lời 1", kn.chot_loi1, lai["tp1"])]
            if lai.get("tp2"):
                rows.append(("Chốt lời 2", kn.chot_loi2, lai["tp2"]))
            rows.append(("Cắt lỗ", kn.cat_lo, lai["sl"]))
            st.markdown(f"**Với {von:,.0f} đ:** mua **{lai['tp1']['so_cp']:,} cổ phiếu** "
                        f"giá {kn.gia_mua:,.0f} = {lai['tp1']['tien_mua']:,.0f} đ (đã gồm phí)")
            st.dataframe(pd.DataFrame([{"Kịch bản": t, "Giá bán": f"{g:,.0f}", "Tiền lãi/lỗ": tien(x["lai"]),
                                        "%": f"{x['pct']:+.1%}"} for t, g, x in rows]),
                         hide_index=True, width="stretch")
        elif lai.get("tp1"):
            st.caption("Số vốn chưa đủ mua 1 lô (100 cổ phiếu).")
    for dong in kn.ly_do:
        st.caption("• " + dong)


def the_tin_hieu_dinh(t, so_luong_dang_giu: float | None = None, gia_von: float | None = None):
    """Thẻ tín hiệu bán ở đỉnh."""
    mau = K.MAU_BAN.get(t.muc, "#64748b")
    st.markdown(
        f"<div style='padding:12px 16px;border-radius:12px;border:2px solid {mau};margin-top:8px'>"
        f"<div style='font-size:13px;color:#64748b'>Tín hiệu bán ở đỉnh ({'khung ngày' if t.tam == 'D' else 'khung tuần'})"
        f" · {t.so_dau_hieu} dấu hiệu</div>"
        f"<div style='font-size:24px;font-weight:700;color:{mau}'>{t.muc}</div>"
        + (f"<div style='font-size:15px'>Vùng bán đẹp: <b>{t.vung_ban[0]:,.0f} – {t.vung_ban[1]:,.0f}</b>"
           f" · đặt bán {t.gia_ban:,.0f}</div>" if t.vung_ban and t.gia_ban else "") + "</div>",
        unsafe_allow_html=True)
    for d in t.dau_hieu:
        st.caption("▼ " + d)


@st.cache_resource
def kho_thi_truong():
    """Kết quả quét dùng chung cho mọi người xem (lưu trong bộ nhớ máy chủ)."""
    return {"luc": None, "ts": 0.0, "D": None, "W": None, "thong_ke": None}


def doc_file_thi_truong(kho):
    if kho["D"] is None and FILE_TT.exists():
        data = json.loads(FILE_TT.read_text(encoding="utf-8"))
        kho.update(luc=data["luc"] + " (bản lưu sẵn)", thong_ke=data["thong_ke"], ts=0.0,
                   **{k: pd.DataFrame(data.get(k, [])) for k in ("D", "W", "ban_D", "ban_W", "nganh_D", "nganh_W")})


def quet_ngay(kho, san, gtgd_min):
    thanh = st.progress(0.0, text="Đang quét…")
    def tt(i, n, ma):
        thanh.progress(i / n, text=f"Đang quét {i}/{n} mã ({ma})")
    kq = quet.quet(san=tuple(san), gtgd_min=gtgd_min, tien_trinh=tt)
    kho.update(luc=pd.Timestamp.now(tz="Asia/Ho_Chi_Minh").strftime("%H:%M %d/%m/%Y"), ts=time.time(),
               thong_ke=quet.thong_ke(kq),
               **{t: quet.bang(kq, t) for t in ("D", "W")},
               **{f"ban_{t}": quet.bang_ban(kq, t) for t in ("D", "W")},
               **{f"nganh_{t}": quet.suc_manh_nganh(kq, t) for t in ("D", "W")})
    thanh.empty()


def tinh_lai_bang(b: pd.DataFrame, von: float) -> pd.DataFrame:
    b = b.copy()
    out = [K.tinh_lai(von, r["Giá mua"], r["Chốt lời"]) if pd.notna(r["Giá mua"]) and pd.notna(r["Chốt lời"])
           else None for _, r in b.iterrows()]
    out_sl = [K.tinh_lai(von, r["Giá mua"], r["Cắt lỗ"]) if pd.notna(r["Giá mua"]) and pd.notna(r["Cắt lỗ"])
              else None for _, r in b.iterrows()]
    b["Số CP"] = [x["so_cp"] if x else None for x in out]
    b["% lãi"] = [round(x["pct"] * 100, 1) if x and x["so_cp"] else None for x in out]
    b["Tiền lãi"] = [round(x["lai"]) if x and x["so_cp"] else None for x in out]
    b["Tiền lỗ"] = [round(x["lai"]) if x and x["so_cp"] else None for x in out_sl]
    return b


# ------------------------------------------------------------------------------------------ doanh nghiệp
@st.cache_data(ttl=6 * 3600, show_spinner=False)
def cb_ho_so(ma):
    return CB.ho_so(ma), CB.co_dong(ma, 10)


@st.cache_data(ttl=6 * 3600, show_spinner=False)
def cb_bctc(ma, phan, quy):
    return CB.bang_bctc(ma, phan, quy)


@st.cache_data(ttl=6 * 3600, show_spinner=False)
def cb_chi_so(ma, quy):
    return CB.bang_chi_so(ma, quy), CB.chi_so_moi_nhat(ma)


@st.cache_data(ttl=3600, show_spinner=False)
def cb_suc_khoe(ma):
    sk = CB.suc_khoe_hien_tai(ma)
    return sk, CB._chuoi_quy(ma)


@st.cache_data(ttl=6 * 3600, show_spinner=False)
def cb_excel(ma):
    import tempfile
    p = Path(tempfile.mkdtemp()) / f"{ma}_tai_chinh.xlsx"
    CB.xuat_excel(ma, p)
    return p.read_bytes()


def sao(x):
    if x is None:
        return "–"
    n = int(round(x))
    return "★" * n + "☆" * (5 - n)


def ty(x):
    return "–" if x is None or pd.isna(x) else f"{x / 1e9:,.0f} tỷ"


def muc_doanh_nghiep(ma):
    hs, cd = cb_ho_so(ma)
    if not hs:
        st.info("Không có thông tin doanh nghiệp cho mã này.")
        return
    st.markdown(f"#### {hs['ten']}")
    st.caption(f"{hs['nganh']} · niêm yết {hs['ngay_niem_yet']}")
    c1, c2, c3 = st.columns(3)
    c1.metric("Vốn hóa", f"{hs['von_hoa'] / 1e12:,.1f} nghìn tỷ" if hs.get("von_hoa") else "–")
    c2.metric("Số cổ phiếu", f"{hs['so_cp'] / 1e6:,.0f} triệu" if hs.get("so_cp") else "–")
    c3.metric("GTGD TB 1 tháng", ty(hs.get("gtgd_tb_1t")))
    c1, c2, c3 = st.columns(3)
    c1.metric("Cao/Thấp 52 tuần", f"{_f(hs.get('cao_52t'))} / {_f(hs.get('thap_52t'))}")
    c2.metric("Nước ngoài sở hữu", f"{hs['nuoc_ngoai']:.1%}" if hs.get("nuoc_ngoai") is not None else "–",
              f"room {hs['room_nuoc_ngoai']:.0%}" if hs.get("room_nuoc_ngoai") else None, delta_color="off")
    c3.metric("Nhà nước sở hữu", f"{hs['nha_nuoc']:.1%}" if hs.get("nha_nuoc") is not None else "–")
    ck = hs.get("ctck")
    if ck:
        st.info(f"**Khuyến nghị của CTCK ({ck['nguon']})**: {ck['xep_hang']} · giá mục tiêu {_f(ck['gia_muc_tieu'])}"
                + (f" (tiềm năng {ck['tiem_nang']:+.0%})" if ck.get("tiem_nang") is not None else "")
                + f" · ngày {ck['ngay']}" + (f" · chuyên viên {ck['chuyen_vien']}" if ck.get("chuyen_vien") else "")
                + ". Đây là ý kiến của bên thứ ba, không phải của công cụ này.")
    if hs.get("gioi_thieu"):
        with st.expander("Giới thiệu doanh nghiệp"):
            st.write(hs["gioi_thieu"])
    if not cd.empty:
        st.markdown("##### Cổ đông lớn")
        st.dataframe(cd.style.format({"Số CP": "{:,.0f}", "Tỷ lệ %": "{:.2f}%"}), hide_index=True, width="stretch")
    mr = cb_mo_rong(ma)
    so = {"Số CP": "{:,.0f}", "Tỷ lệ %": "{:.3f}%", "Sở hữu %": "{:.2f}%", "Vốn điều lệ (tỷ)": "{:,.1f}",
          "Vốn góp (tỷ)": "{:,.1f}", "Cổ tức %": "{:.2f}%", "Tiền/CP (đ)": "{:,.0f}", "Đăng ký": "{:,.0f}",
          "Thực hiện": "{:,.0f}", "Sở hữu sau GD": "{:,.0f}"}
    for tieu_de, k in (("Ban lãnh đạo", "bld"), ("Công ty con, liên kết", "con"), ("Lịch sử trả cổ tức", "cotuc"),
                       ("Sự kiện doanh nghiệp", "sukien"), ("Giao dịch nội bộ", "noibo")):
        b = mr.get(k)
        if b is not None and not b.empty:
            with st.expander(f"{tieu_de} ({len(b)})", expanded=k in ("cotuc",)):
                st.dataframe(b.style.format({c: f for c, f in so.items() if c in b}, na_rep="–"),
                             hide_index=True, width="stretch")
    st.caption("Công ty kiểm toán: chưa có nguồn dữ liệu công khai lấy được tự động.")


@st.cache_data(ttl=6 * 3600, show_spinner=False)
def cb_mo_rong(ma):
    """Ban lãnh đạo, công ty con, cổ tức, sự kiện, giao dịch nội bộ (mỗi mục lỗi riêng không ảnh hưởng mục khác)."""
    out = {}
    for k, ham in (("bld", CB.ban_lanh_dao), ("con", CB.cong_ty_con), ("cotuc", lambda m: CB.lich_su_co_tuc(m, 20)),
                   ("sukien", lambda m: CB.su_kien(m, 30)), ("noibo", lambda m: CB.giao_dich_noi_bo(m, 30))):
        try:
            out[k] = ham(ma)
        except Exception:
            out[k] = pd.DataFrame()
    return out


@st.cache_data(ttl=15 * 60, show_spinner=False)
def tin_ma(ma, ten):
    ds = TT.tin_theo_ma(ma, ten)
    try:
        dn = CB.tin_doanh_nghiep(ma, 15)
    except Exception:
        dn = []
    return ds, dn


@st.cache_data(ttl=15 * 60, show_spinner=False)
def tin_cho(nguon: tuple):
    return TT.tin_thi_truong(list(nguon))


MAU_TIN = {1: "#16a34a", -1: "#dc2626", 0: "#64748b"}


def hien_tin(ds, so=30, key=""):
    if not ds:
        st.caption("Chưa có tin.")
        return
    for t in ds[:so]:
        tg = t.thoi_gian.strftime("%d/%m %H:%M") if t.thoi_gian is not None else ""
        nhan = f"<span style='color:{MAU_TIN[t.cam_xuc]};font-weight:600'>{t.nhan}</span>" if t.cam_xuc else ""
        ma = " ".join(f"<code>{m}</code>" for m in t.ma[:4])
        st.markdown(f"<div style='padding:6px 0;border-bottom:1px solid #e2e8f0'>"
                    f"<a href='{html_esc(t.link)}' target='_blank'>{html_esc(t.tieu_de)}</a><br>"
                    f"<span style='font-size:12px;color:#64748b'>{tg} · {html_esc(t.nguon)}</span> {nhan} {ma}</div>",
                    unsafe_allow_html=True)


def html_esc(s):
    import html
    return html.escape(str(s or ""), quote=True)


def muc_tin_tuc(ma, ten):
    with st.spinner("Đang tìm tin…"):
        ds, dn = tin_ma(ma, ten)
    st.caption("Tin từ nhiều báo (Google News). Nhãn Tích cực/Tiêu cực tự động theo từ khóa – chỉ để tham khảo.")
    dem = {k: sum(t.cam_xuc == k for t in ds) for k in (1, -1)}
    c1, c2, c3 = st.columns(3)
    c1.metric("Tin gần đây", len(ds))
    c2.metric("Tích cực", dem[1])
    c3.metric("Tiêu cực", dem[-1])
    hien_tin(ds, 25)
    if dn:
        st.markdown("##### Tin & công bố của doanh nghiệp")
        for x in dn:
            st.markdown(f"- **{x['ngay']}** · {html_esc(x['tieu_de'])}" + (f" ([nguồn]({x['link']}))" if x["link"] else ""))


def muc_tai_chinh(ma):
    try:
        sk, quy = cb_suc_khoe(ma)
    except Exception as e:
        st.info(f"Không có báo cáo tài chính: {e}")
        return
    if not quy.empty:
        import plotly.graph_objects as go
        q = quy.tail(8)
        fig = go.Figure()
        fig.add_bar(x=q["ky"], y=q["dt"] / 1e9, name="Doanh thu (tỷ)", marker_color="#93c5fd")
        fig.add_bar(x=q["ky"], y=q["ln"] / 1e9, name="Lợi nhuận (tỷ)", marker_color="#2563eb")
        fig.update_layout(barmode="group", height=300, margin=dict(l=8, r=8, t=30, b=8), template="plotly_white",
                          title="Doanh thu & lợi nhuận theo quý", legend=dict(orientation="h", y=-0.2))
        st.plotly_chart(fig, width="stretch", key=f"bctc_bd_{ma}")
    c1, c2 = st.columns(2)
    phan = c1.selectbox("Báo cáo", list(CB.TEN_PHAN), format_func=CB.TEN_PHAN.get, key=f"bctc_phan_{ma}")
    ky = c2.radio("Kỳ", ["Năm", "Quý"], horizontal=True, key=f"bctc_ky_{ma}")
    b = cb_bctc(ma, phan, ky == "Quý")
    if b.empty:
        st.info("Không có dữ liệu.")
    else:
        st.caption("Đơn vị: tỷ đồng (EPS: đồng)")
        st.dataframe(b.drop(columns="_ma").set_index("Chỉ tiêu").style.format("{:,.1f}", na_rep="–"),
                     width="stretch", height=480)
    st.download_button("⬇ Tải BCTC & chỉ số (Excel)", cb_excel(ma), file_name=f"{ma}_tai_chinh.xlsx",
                       width="stretch", key=f"bctc_xlsx_{ma}")


def muc_chi_so(ma):
    try:
        sk, _ = cb_suc_khoe(ma)
        bang_q, moi = cb_chi_so(ma, True)
    except Exception as e:
        st.info(f"Không có chỉ số tài chính: {e}")
        return
    if sk.du_lieu:
        st.markdown(f"#### Sức khỏe tài chính: {sk.tong}/5")
        c1, c2 = st.columns(2)
        c1.markdown(f"Tăng trưởng **{sao(sk.tang_truong)}**  \nSinh lời **{sao(sk.sinh_loi)}**")
        c2.markdown(f"An toàn tài chính **{sao(sk.an_toan)}**  \nĐịnh giá **{sao(sk.dinh_gia)}**")
        for d in sk.ly_do:
            st.caption("• " + d)
        with st.expander("Cách chấm sao"):
            st.markdown(
                "- **Tăng trưởng**: lợi nhuận & doanh thu 4 quý gần nhất so với 4 quý trước (giảm >20% → 1★, "
                "tăng >25% → 5★).\n- **Sinh lời**: ROE (<5% → 1★, ≥20% → 5★; đang lỗ → 1★).\n"
                "- **An toàn**: nợ vay/vốn chủ (>2 lần → 1★, ≤0,5 → 5★); ngân hàng: vốn chủ/tổng tài sản.\n"
                "- **Định giá**: P/E hiện tại so với P/E của chính mã đó 3 năm qua (rẻ nhất 20% → 5★).\n"
                "Chỉ dùng báo cáo đã công bố. Điểm tổng = trung bình 4 mục.")
    else:
        st.caption(" · ".join(sk.ly_do))
    if moi:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("P/E", f"{moi['pe']:.1f}" if moi.get("pe") else "–")
        c2.metric("P/B", f"{moi['pb']:.2f}" if moi.get("pb") else "–")
        c3.metric("ROE", f"{moi['roe']:.1%}" if moi.get("roe") else "–")
        c4.metric("Cổ tức", f"{moi['dividendYield']:.1%}" if moi.get("dividendYield") else "–")
        if moi.get("pe_lich_su") and moi.get("pe"):
            ls = moi["pe_lich_su"]
            st.caption(f"P/E 5 năm: thấp nhất {min(ls):.1f} · trung vị {pd.Series(ls).median():.1f} · cao nhất {max(ls):.1f}")
    ky = st.radio("Kỳ", ["Quý (4 quý gần nhất)", "Năm"], horizontal=True, key=f"cs_ky_{ma}")
    b = bang_q if ky.startswith("Quý") else cb_chi_so(ma, False)[0]
    if not b.empty:
        st.caption("Đơn vị: % với ROE, ROA, biên LN, cổ tức, NIM, NPL, CASA; lần (x) với P/E, P/B, nợ.")
        st.dataframe(b.set_index("Chỉ số").style.format("{:,.2f}", na_rep="–"), width="stretch")


# ------------------------------------------------------------------------------------------ giao diện
st.markdown("### 📈 Dự đoán xu hướng & khuyến nghị")
st.caption("Stoch · MACD · MFI · ADX · ICT · SMC · Fibonacci · LEVEL 1")

with st.expander("⚙ Cài đặt chung", expanded=False):
    tam_nhan = st.radio("Tầm nắm giữ", list(TAM), horizontal=True)
    von = st.number_input("Số vốn cho mỗi lệnh (đồng)", min_value=1_000_000, value=100_000_000,
                          step=10_000_000, format="%d")
tam = TAM[tam_nhan]

tab0, tab_loc, tab1, tab_tin, tab2, tab3 = st.tabs(["🏆 Khuyến nghị", "🔎 Bộ lọc", "🔍 Tra cứu", "📰 Tin thị trường",
                                                    "💼 Danh mục", "📋 Theo dõi"])
mac_dinh = du_lieu.doc_danh_sach(HERE / "ma.txt")

with tab0:
    kho = kho_thi_truong()
    doc_file_thi_truong(kho)
    c1, c2 = st.columns(2)
    san = c1.multiselect("Sàn", ["HSX", "HNX", "UPCOM"], default=["HSX", "HNX", "UPCOM"],
                         format_func=lambda x: du_lieu.SAN[x])
    gtgd_ty = c2.number_input("GTGD tối thiểu (tỷ đồng/phiên)", min_value=0.0, value=1.0, step=0.5)
    cu = time.time() - kho["ts"] > 3600
    if st.button("🔄 Quét toàn thị trường" + (" (~3–7 phút)" if cu else ""), type="primary", width="stretch"):
        quet_ngay(kho, san or ["HSX"], gtgd_ty * 1e9)
    if kho[tam] is None:
        st.info("Chưa có dữ liệu – bấm **Quét toàn thị trường**.")
    else:
        tk = kho["thong_ke"]
        st.caption(f"Cập nhật {kho['luc']} · quét {tk['tong']} mã · phân tích {tk['phan_tich']} mã đủ thanh khoản "
                   f"· {tk['tang']} tăng / {tk['giam']} giảm")
        xem = st.radio("Xem", ["🟢 Nên mua", "🔴 Bán ở đỉnh", "🏭 Sức mạnh ngành"], horizontal=True,
                       label_visibility="collapsed", key="xem")
        ng = kho.get(f"nganh_{tam}")
        ds_nganh = ng["Ngành"].tolist() if ng is not None and not ng.empty else []
        loc_nganh = st.multiselect("Ngành", ds_nganh, placeholder="Tất cả ngành", key="loc_nganh") if xem != "🏭 Sức mạnh ngành" else []

        def loc(b):
            if b is None or b.empty:
                return pd.DataFrame()
            b = b[b["Sàn"].isin([du_lieu.SAN[x] for x in san])] if san else b
            b = b[b["GTGD (tỷ)"].fillna(0) >= gtgd_ty]
            if loc_nganh and "Ngành" in b:
                b = b[b["Ngành"].isin(loc_nganh)]
            return b

        chon = None
        if xem == "🟢 Nên mua":
            b = loc(tinh_lai_bang(kho[tam], von))
            muc = st.multiselect("Lọc khuyến nghị", K.MUC[::-1], default=["Mua mạnh", "Mua", "Chờ về vùng mua"])
            b = b[b["Khuyến nghị"].isin(muc)] if not b.empty else b
            dem = b["Khuyến nghị"].value_counts() if not b.empty else {}
            for col, m in zip(st.columns(3), ["Mua mạnh", "Mua", "Chờ về vùng mua"]):
                col.metric(m, int(dem.get(m, 0)))
            if not b.empty:
                cot = [c for c in ["Mã", "Ngành", "Khuyến nghị", "Giá", "Vùng mua", "Giá mua", "Cắt lỗ", "Chốt lời",
                                   "R:R", "% lãi", "Tiền lãi", "Tiền lỗ", "Số CP", "Sức khỏe", "P/E", "ROE %",
                                   "Tăng LN %", "CTCK", "Ngành mạnh/yếu", "Tín hiệu đỉnh", "GTGD (tỷ)"] if c in b]
                hien = b[cot]
                st.dataframe(hien.style.map(lambda v: f"color:{K.MAU_MUC.get(v, '#000')};font-weight:600",
                                            subset=["Khuyến nghị"]).format(
                    {"Giá": "{:,.0f}", "Giá mua": "{:,.0f}", "Cắt lỗ": "{:,.0f}", "Chốt lời": "{:,.0f}",
                     "Tiền lãi": "{:,.0f}", "Tiền lỗ": "{:,.0f}", "Số CP": "{:,.0f}", "R:R": "{:.1f}",
                     "% lãi": "{:+.1f}%", "GTGD (tỷ)": "{:,.1f}", "Sức khỏe": "{:.1f}", "P/E": "{:.1f}",
                     "ROE %": "{:.1f}", "Tăng LN %": "{:+.0f}"}, na_rep="–"),
                    hide_index=True, width="stretch", height=420)
                st.download_button("⬇ Tải bảng (CSV)", hien.to_csv(index=False).encode("utf-8-sig"),
                                   file_name=f"nen_mua_{tam}.csv", mime="text/csv", width="stretch")
                chon = st.selectbox("Xem chi tiết mã", b["Mã"].tolist(), key="chon_kn")
        elif xem == "🔴 Bán ở đỉnh":
            b = loc(kho.get(f"ban_{tam}"))
            muc = st.multiselect("Lọc tín hiệu", K.MUC_BAN[:0:-1], default=["Bán mạnh", "Chốt lời dần", "Theo dõi đỉnh"])
            b = b[b["Tín hiệu"].isin(muc)] if not b.empty else b
            dem = b["Tín hiệu"].value_counts() if not b.empty else {}
            for col, m in zip(st.columns(3), ["Bán mạnh", "Chốt lời dần", "Theo dõi đỉnh"]):
                col.metric(m, int(dem.get(m, 0)))
            st.caption("Cổ phiếu VN không bán khống được: đây là gợi ý CHỐT LỜI / thoát hàng cho mã đang nắm giữ.")
            if b.empty:
                st.info("Hiện chưa có mã nào ở vùng đỉnh theo bộ lọc này.")
            else:
                hien = b[["Mã", "Ngành", "Tín hiệu", "Số dấu hiệu", "Giá", "% 20 phiên", "Vùng bán", "Giá bán",
                          "Đỉnh gần nhất", "GTGD (tỷ)", "Dấu hiệu"]]
                st.dataframe(hien.style.map(lambda v: f"color:{K.MAU_BAN.get(v, '#000')};font-weight:600",
                                            subset=["Tín hiệu"]).format(
                    {"Giá": "{:,.0f}", "Giá bán": "{:,.0f}", "Đỉnh gần nhất": "{:,.0f}", "% 20 phiên": "{:+.1f}%",
                     "GTGD (tỷ)": "{:,.1f}"}, na_rep="–"), hide_index=True, width="stretch", height=420)
                st.download_button("⬇ Tải bảng (CSV)", hien.to_csv(index=False).encode("utf-8-sig"),
                                   file_name=f"ban_dinh_{tam}.csv", mime="text/csv", width="stretch")
                chon = st.selectbox("Xem chi tiết mã", b["Mã"].tolist(), key="chon_ban")
        else:
            if ng is None or ng.empty:
                st.info("Bấm **Quét toàn thị trường** để xếp hạng ngành.")
            else:
                st.caption("Sức mạnh = điểm xu hướng TB, tỷ lệ mã tăng/giảm và hiệu suất 20 phiên. "
                           "Mã thuộc ngành Mạnh được cộng 10 điểm khi xếp hạng mua, ngành Yếu bị trừ 10.")
                mau_xl = {"Mạnh": "color:#16a34a;font-weight:600", "Yếu": "color:#dc2626;font-weight:600"}
                st.dataframe(ng.style.map(lambda v: mau_xl.get(v, ""), subset=["Xếp loại"]).format(
                    {"Điểm TB": "{:+.1f}", "Hiệu suất 20 phiên %": "{:+.1f}%", "Sức mạnh": "{:+.1f}",
                     "GTGD (tỷ)": "{:,.0f}"}), hide_index=True, width="stretch", height=560)
        if chon:
            with st.spinner(f"Đang phân tích {chon}…"):
                kq, _, _ = phan_tich(chon, False)
            if kq.khung:
                kn = K.khuyen_nghi(kq, tam)
                try:
                    CB.dieu_chinh_khuyen_nghi(kn, CB.tom_tat_co_ban(kq.ma, kq.frames.get("D")))
                except Exception:
                    pass
                the_khuyen_nghi(kn, von)
                the_tin_hieu_dinh(K.tin_hieu_dinh(kq, tam))
                with st.expander("🏢 Doanh nghiệp & chỉ số tài chính"):
                    muc_chi_so(kq.ma)
                chi_tiet(kq, None, "khuyen_nghi")

with tab1:
    with st.form("tra_cuu"):
        ma = st.text_input("Mã (VD: FPT, VNINDEX, EURUSD, XAUUSD, AAPL)", value=st.session_state.get("ma", "FPT"))
        thu_lai = st.checkbox("Thử lại trên quá khứ (chậm hơn)", value=True)
        ok = st.form_submit_button("Phân tích", type="primary", width="stretch")
    if ok:
        st.session_state["ma"] = ma.strip().upper()
    ma = st.session_state.get("ma", "FPT")
    if ma:
        with st.spinner(f"Đang phân tích {ma}…"):
            kq, _, tl = phan_tich(ma, thu_lai)
        if kq.khung and kq.loai == "vn" and kq.ma in du_lieu.CHI_SO_VN and tam in kq.frames:
            st.caption("Chỉ số không mua/bán trực tiếp được – chỉ xem xu hướng và tín hiệu đỉnh.")
            the_tin_hieu_dinh(K.tin_hieu_dinh(kq, tam))
        elif kq.khung and kq.loai == "vn" and tam in kq.frames:
            t_kt, t_dn, t_tc, t_cs, t_tin = st.tabs(["📈 Kỹ thuật", "🏢 Doanh nghiệp", "📊 Tài chính", "🧮 Chỉ số",
                                                    "📰 Tin tức"])
            with t_dn:
                muc_doanh_nghiep(kq.ma)
            with t_tin:
                try:
                    ten = (cb_ho_so(kq.ma)[0] or {}).get("ten_ngan")
                except Exception:
                    ten = None
                muc_tin_tuc(kq.ma, ten)
            with t_tc:
                muc_tai_chinh(kq.ma)
            with t_cs:
                muc_chi_so(kq.ma)
            with t_kt:
                kn = K.khuyen_nghi(kq, tam)
                try:
                    CB.dieu_chinh_khuyen_nghi(kn, CB.tom_tat_co_ban(kq.ma, kq.frames.get("D")))
                except Exception:
                    pass
                the_khuyen_nghi(kn, von)
                the_tin_hieu_dinh(K.tin_hieu_dinh(kq, tam))
                chi_tiet(kq, tl, "tra_cuu")
            kq = None
        elif kq.khung:
            st.caption("Khuyến nghị mua & máy tính lãi/lỗ áp dụng cho cổ phiếu Việt Nam.")
            khung_dinh = "4H" if kq.loai == "fx" else "D"
            if khung_dinh in kq.frames:
                the_tin_hieu_dinh(K.tin_hieu_dinh(kq, khung_dinh, loai=kq.loai))
        if kq is not None:
            chi_tiet(kq, tl, "tra_cuu")

with tab_loc:
    kho = kho_thi_truong()
    doc_file_thi_truong(kho)
    b0 = kho.get(tam)
    if b0 is None or b0.empty or "Sức khỏe" not in b0:
        st.info("Chưa có số liệu cơ bản – vào tab **Khuyến nghị** bấm **Quét toàn thị trường**.")
    else:
        st.caption(f"Lọc {len(b0)} mã đủ thanh khoản theo số liệu cơ bản + kỹ thuật (cập nhật {kho['luc']}).")
        c1, c2 = st.columns(2)
        pe_max = c1.number_input("P/E tối đa", 0.0, 200.0, 20.0, 1.0)
        roe_min = c2.number_input("ROE tối thiểu (%)", -50.0, 100.0, 10.0, 1.0)
        ln_min = c1.number_input("Tăng trưởng LN tối thiểu (%)", -100.0, 500.0, 0.0, 5.0)
        no_max = c2.number_input("Nợ vay/Vốn chủ tối đa (lần)", 0.0, 20.0, 2.0, 0.1)
        sk_min = c1.slider("Sức khỏe tài chính tối thiểu", 1.0, 5.0, 3.0, 0.5)
        bo_lo = c2.checkbox("Bỏ doanh nghiệp đang lỗ", value=True)
        chi_ctck = c2.checkbox("Chỉ mã CTCK khuyến nghị MUA", value=False)
        kt = st.multiselect("Khuyến nghị kỹ thuật", K.MUC[::-1], default=K.MUC[::-1], key="loc_kt")
        b = b0.copy()
        b = b[(b["P/E"].isna() | (b["P/E"] <= pe_max)) & (b["P/E"].fillna(1) > 0)]
        b = b[b["ROE %"].fillna(-999) >= roe_min] if roe_min > -50 else b
        b = b[b["Tăng LN %"].fillna(-999) >= ln_min] if ln_min > -100 else b
        b = b[b["Nợ/VCSH"].isna() | (b["Nợ/VCSH"] <= no_max)]
        b = b[b["Sức khỏe"].fillna(0) >= sk_min]
        if bo_lo:
            b = b[b["Đang lỗ"] != True]  # noqa: E712
        if chi_ctck:
            b = b[b["CTCK"] == "MUA"]
        b = b[b["Khuyến nghị"].isin(kt)]
        st.metric("Số mã đạt", len(b))
        cot = [c for c in ["Mã", "Ngành", "Khuyến nghị", "Giá", "P/E", "P/B", "ROE %", "Tăng LN %", "Tăng DT %",
                           "Nợ/VCSH", "Cổ tức %", "Sức khỏe", "CTCK", "Giá mục tiêu", "Giá mua", "Chốt lời", "R:R",
                           "GTGD (tỷ)"] if c in b]
        st.dataframe(b[cot].sort_values(["Sức khỏe", "ROE %"], ascending=False).style.format(
            {"Giá": "{:,.0f}", "Giá mua": "{:,.0f}", "Chốt lời": "{:,.0f}", "Giá mục tiêu": "{:,.0f}",
             "P/E": "{:.1f}", "P/B": "{:.2f}", "ROE %": "{:.1f}", "Tăng LN %": "{:+.0f}", "Tăng DT %": "{:+.0f}",
             "Nợ/VCSH": "{:.2f}", "Cổ tức %": "{:.1f}", "Sức khỏe": "{:.1f}", "R:R": "{:.1f}",
             "GTGD (tỷ)": "{:,.1f}"}, na_rep="–"), hide_index=True, width="stretch", height=480)
        st.download_button("⬇ Tải kết quả lọc (CSV)", b[cot].to_csv(index=False).encode("utf-8-sig"),
                           file_name="bo_loc.csv", mime="text/csv", width="stretch")

with tab_tin:
    c1, c2 = st.columns(2)
    nguon = c1.multiselect("Nguồn", list(TT.RSS), default=list(TT.RSS), key="tin_nguon")
    danh_gia = c2.multiselect("Đánh giá", ["Tích cực", "Tiêu cực", "Trung tính"],
                              default=["Tích cực", "Tiêu cực", "Trung tính"], key="tin_dg")
    tu_khoa = st.text_input("Tìm theo từ khóa hoặc mã (VD: HPG, lãi suất, ngân hàng)", key="tin_tk")
    chi_co_ma = st.checkbox("Chỉ tin có nhắc tới mã cổ phiếu", key="tin_ma")
    if st.button("🔄 Làm mới tin", key="tin_lm"):
        tin_cho.clear()
    with st.spinner("Đang tải tin…"):
        ds_tin = tin_cho(tuple(nguon))
    tk = tu_khoa.strip()
    loc = [t for t in ds_tin if t.nhan in danh_gia and (not chi_co_ma or t.ma)
           and (not tk or tk.lower() in t.tieu_de.lower() or tk.upper() in t.ma)]
    st.caption(f"{len(loc)}/{len(ds_tin)} tin · tự làm mới mỗi 15 phút · nhãn đánh giá tự động theo từ khóa")
    hien_tin(loc, 80)

with tab2:
    st.caption("Nhập các mã đang nắm giữ. Khi chạy trên máy tính, danh mục được lưu vào danh_muc.csv; "
               "trên web hãy tải file về để lưu.")
    if "dm" not in st.session_state:
        st.session_state["dm"] = (pd.read_csv(FILE_DM) if FILE_DM.exists() else
                                  pd.DataFrame({"Mã": ["FPT"], "Giá mua": [50000.0], "Số lượng": [1000]}))
    up = st.file_uploader("Mở file danh mục (.csv)", type="csv")
    if up is not None:
        st.session_state["dm"] = pd.read_csv(up)
    dm = st.data_editor(st.session_state["dm"], num_rows="dynamic", width="stretch", key="dm_editor",
                        column_config={"Giá mua": st.column_config.NumberColumn(format="%.0f"),
                                       "Số lượng": st.column_config.NumberColumn(format="%d")})
    c1, c2 = st.columns(2)
    if c1.button("💾 Lưu", width="stretch"):
        try:
            dm.to_csv(FILE_DM, index=False)
            st.success("Đã lưu danh_muc.csv")
        except OSError:
            st.warning("Không lưu được trên máy chủ – hãy dùng nút Tải về.")
    c2.download_button("⬇ Tải về", dm.to_csv(index=False).encode("utf-8-sig"), "danh_muc.csv", "text/csv",
                       width="stretch")
    rows, tong_von, tong_lai = [], 0.0, 0.0
    for _, r in dm.dropna(subset=["Mã"]).iterrows():
        m = str(r["Mã"]).strip().upper()
        if not m or pd.isna(r.get("Giá mua")) or pd.isna(r.get("Số lượng")):
            continue
        kq, _, _ = phan_tich(m, False)
        kn = K.khuyen_nghi(kq, tam) if kq.khung and tam in kq.frames else None
        dinh = K.tin_hieu_dinh(kq, tam) if kq.khung and tam in kq.frames else None
        v = K.danh_gia_vi_the(float(r["Giá mua"]), float(r["Số lượng"]), kq, kn, dinh=dinh)
        if v["lai"] is not None:
            tong_von += float(r["Giá mua"]) * float(r["Số lượng"])
            tong_lai += v["lai"]
        rows.append({"Mã": m, "Giá mua": r["Giá mua"], "Giá hiện tại": v["gia"], "Số lượng": r["Số lượng"],
                     "Lãi/lỗ": v["lai"], "%": v["pct"] * 100 if v["pct"] is not None else None,
                     "Gợi ý": v["goi_y"], "Tín hiệu đỉnh": dinh.muc if dinh else "–",
                     "Giá bán đề xuất": v["gia_ban"], "Lãi nếu bán": v["lai_neu_ban"],
                     "Cắt lỗ động": v["cat_lo"], "Chốt lời": kn.chot_loi1 if kn else None})
    if rows:
        c1, c2 = st.columns(2)
        c1.metric("Tổng vốn", tien(tong_von))
        c2.metric("Lãi/lỗ (sau phí, thuế)", tien(tong_lai), f"{tong_lai / tong_von:+.1%}" if tong_von else None)
        def mau_lai(v):
            return "" if v is None or pd.isna(v) else ("color:#16a34a" if v > 0 else "color:#dc2626")
        st.dataframe(pd.DataFrame(rows).style.map(mau_lai, subset=["Lãi/lỗ", "%"]).format(
            {"Giá mua": "{:,.0f}", "Giá hiện tại": "{:,.0f}", "Số lượng": "{:,.0f}", "Lãi/lỗ": "{:,.0f}",
             "%": "{:+.1f}%", "Cắt lỗ động": "{:,.0f}", "Chốt lời": "{:,.0f}", "Giá bán đề xuất": "{:,.0f}",
             "Lãi nếu bán": "{:,.0f}"}, na_rep="–"),
            hide_index=True, width="stretch")
        st.markdown("##### Tin mới của các mã đang giữ")
        tin_dm = []
        for r in rows:
            if r["Mã"] in du_lieu.CHI_SO_VN or du_lieu.phan_loai(r["Mã"])[0] != "vn":
                continue
            try:
                tin_dm += [t for t in tin_ma(r["Mã"], None)[0][:5]]
            except Exception:
                pass
        tin_dm.sort(key=lambda t: t.thoi_gian or pd.Timestamp(0, tz="Asia/Ho_Chi_Minh"), reverse=True)
        xau = [t for t in tin_dm if t.cam_xuc < 0]
        if xau:
            st.warning(f"⚠ {len(xau)} tin tiêu cực gần đây liên quan đến mã đang giữ – xem bên dưới.")
        hien_tin(tin_dm, 20)

with tab3:
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
