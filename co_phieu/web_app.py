"""Web app dự đoán xu hướng – mở được trên điện thoại.

Chạy trên máy:      py -m streamlit run web_app.py   (hoặc bấm run_web.bat)
Đưa lên mạng:       Streamlit Community Cloud, file chính co_phieu/web_app.py
"""
import json
import math
import os
import sys
import time
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from dudoan import bao_cao, co_ban as CB, du_lieu, forex as FX, greenview as G, mo_hinh as MH, khuyen_nghi as K, lich_su as LS, quet, tin_tuc as TT  # noqa: E402
from du_doan import phan_tich_ma  # noqa: E402

st.set_page_config(page_title="Dự đoán xu hướng", page_icon="📈", layout="centered")

MAU = {1: "#16a34a", -1: "#dc2626", 0: "#64748b"}
MUI_TEN = bao_cao.MUI_TEN
_f = bao_cao._f


@st.cache_data(ttl=1800, show_spinner=False)
def gv_goi(ma: str) -> dict:
    """Dữ liệu cho GreenView (giá ngày + kế hoạch + tín hiệu quá khứ), dùng lại trong 30 phút."""
    return G.goi_du_lieu(ma)


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


def chi_tiet(kq, tl, tab: str, dau: bool = True):
    """Chi tiết kỹ thuật. dau=False: bỏ thẻ kết quả + kế hoạch Fibonacci (đã có thẻ kết luận ở trên)."""
    if dau:
        the_ket_qua(kq)
    if not kq.khung:
        for g in kq.ghi_chu:
            st.error(g)
        return
    if dau:
        ke_hoach_fibo(kq, tl)
    else:
        for g in kq.ghi_chu:
            st.caption("• " + g)
    st.markdown("##### Các khung thời gian")
    for k in kq.khung:
        with st.expander(f"{MUI_TEN[k.xu_huong]} Khung {k.khung}: {k.nhan} ({k.diem:+.0f})"):
            for v in k.votes:
                dau_ = MUI_TEN[(v.gia_tri > 0) - (v.gia_tri < 0)]
                st.markdown(f"{dau_} **{v.ten}**: {v.ly_do}")
            for g in k.ghi_chu:
                st.caption("• " + g)
    bieu_do_plotly(kq, tab)


def ke_hoach_fibo(kq, tl):
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


def bieu_do_plotly(kq, tab):
    st.markdown("##### Biểu đồ")
    if st.toggle("Xem bằng GreenView (kèm vùng mua, cắt lỗ, chốt lời và các lần báo Mua trước đây)",
                 key=f"gv_{tab}_{kq.ma}"):
        with st.spinner("Đang dựng GreenView (lần đầu ~10–20 giây)…"):
            try:
                html = G.html_nhung(gv_goi(kq.ma))
            except Exception as e:
                html = None
                st.info(f"Chưa mở được GreenView cho {kq.ma}: {str(e)[:150]}")
        if html:
            components.html(html, height=720, scrolling=False)
            st.caption("Kéo để xem lại quá khứ, chụm 2 ngón để phóng to. Bảng \"Kiểm tra chiến lược\": "
                       "Chỉ báo › StockPredict › \"StockPredict — Dự đoán xu hướng\".")
        return
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
# Thư mục báo cáo (đổi được bằng biến môi trường CO_PHIEU_BAO_CAO – test dùng thư mục tạm, không ghi đè dữ liệu thật)
BAO_CAO = Path(os.environ.get("CO_PHIEU_BAO_CAO", HERE / "bao_cao"))
FILE_TT = BAO_CAO / "thi_truong.json"
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
        tg = kn.thoi_gian
        if tg is not None and tg.thuong is not None:
            dong = f"⏱ **Dự kiến chạm chốt lời** (theo tốc độ các nhịp tăng trước): {tg.mo_ta()}"
            if tg.fibo:
                f = lambda d: d.strftime("%d/%m/%Y") if d is not None else "?"  # noqa: E731
                dong += (f"  \n⏱ Theo Fibonacci thời gian: {f(tg.ngay(tg.fibo[0]))} / {f(tg.ngay(tg.fibo[1]))} / "
                         f"{f(tg.ngay(tg.fibo[2]))} (0.618 / 1 / 1.618 × nhịp trước – kiểm định cho thấy "
                         f"thường quá sớm, độ tin cậy thấp)")
            st.markdown(dong)
            st.caption("Ngày tính theo phiên giao dịch (bỏ thứ 7, CN; chưa trừ ngày lễ). Kiểm định 2 năm: khoảng 50% "
                       "lệnh chạm chốt lời nằm trong khoảng dự kiến, sai số trung vị ~7–8 phiên. Chỉ là ước lượng.")
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
    try:
        quet.ghi(BAO_CAO, kq)            # cũng lưu bản khuyến nghị của ngày (tab "Theo ngày")
    except Exception:
        pass
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


def loi_nguon(e, muc: str):
    """Thông báo thân thiện khi một nguồn dữ liệu phụ bị lỗi (app vẫn chạy tiếp)."""
    ma_loi = getattr(e, "code", None)
    goi_y = {403: "nguồn từ chối truy cập từ máy chủ này", 429: "gọi quá nhiều lần, thử lại sau ít phút",
             404: "không có dữ liệu cho mã này"}.get(ma_loi, "lỗi kết nối")
    st.info(f"Chưa lấy được {muc}: {goi_y}" + (f" (mã lỗi {ma_loi})" if ma_loi else f" ({type(e).__name__})")
            + ". Các phần khác vẫn dùng bình thường.")


def sao(x):
    if x is None:
        return "–"
    n = int(round(x))
    return "★" * n + "☆" * (5 - n)


def ty(x):
    return "–" if x is None or pd.isna(x) else f"{x / 1e9:,.0f} tỷ"


@st.cache_data(ttl=6 * 3600, show_spinner=False)
def cb_vnd(ma):
    return CB.tom_tat_vnd(ma)


def hien_tom_tat_vnd(ma, phan: str):
    """Nguồn chính (Vietcap) bị chặn → hiện bản tóm tắt từ VNDirect."""
    try:
        t = cb_vnd(ma)
    except Exception as e:
        loi_nguon(e, "thông tin doanh nghiệp")
        return
    if phan == "dn":
        st.markdown(f"#### {t['ten']}")
        st.caption(" · ".join(x for x in [t.get("san"), f"thành lập {t['thanh_lap']}" if t.get("thanh_lap") else "",
                                          t.get("website")] if x))
        if t.get("von_hoa"):
            st.metric("Vốn hóa", f"{t['von_hoa'] / 1e12:,.1f} nghìn tỷ")
        if t.get("gioi_thieu"):
            with st.expander("Giới thiệu doanh nghiệp"):
                st.write(t["gioi_thieu"])
    else:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("P/E", f"{t['pe']:.1f}" if t.get("pe") else "–")
        c2.metric("P/B", f"{t['pb']:.2f}" if t.get("pb") else "–")
        c3.metric("ROE", f"{t['roe']:.1%}" if t.get("roe") else "–")
        c4.metric("Cổ tức", f"{t['co_tuc']:.1%}" if t.get("co_tuc") else "–")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("EPS", f"{t['eps']:,.0f}" if t.get("eps") else "–")
        c2.metric("Giá trị sổ sách/CP", f"{t['bvps']:,.0f}" if t.get("bvps") else "–")
        c3.metric("ROA", f"{t['roa']:.1%}" if t.get("roa") else "–")
        c4.metric("Beta", f"{t['beta']:.2f}" if t.get("beta") else "–")
    st.caption("Bản tóm tắt từ VNDirect (nguồn chính tạm không truy cập được từ máy chủ này)"
               + (f", số liệu ngày {t['ngay_chi_so']}" if t.get("ngay_chi_so") else "") + ".")


def muc_doanh_nghiep(ma):
    try:
        hs, cd = cb_ho_so(ma)
    except Exception:
        hien_tom_tat_vnd(ma, "dn")
        return
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
    try:
        mr = cb_mo_rong(ma)
    except Exception as e:
        loi_nguon(e, "hồ sơ mở rộng")
        mr = {}
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
def tin_cho(nguon: tuple, nhom: str = "Chứng khoán"):
    return TT.tin_thi_truong(list(nguon), nhom)


@st.cache_data(ttl=15 * 60, show_spinner=False)
def tin_chu_de(chu_de: str):
    return TT.tin_chu_de(chu_de)


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
    try:
        with st.spinner("Đang tìm tin…"):
            ds, dn = tin_ma(ma, ten)
    except Exception as e:
        loi_nguon(e, "tin tức")
        return
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


def muc_tai_chinh(ma, noi="tc"):
    try:
        sk, quy = cb_suc_khoe(ma)
    except Exception as e:
        loi_nguon(e, "báo cáo tài chính chi tiết")
        return
    if not quy.empty:
        import plotly.graph_objects as go
        q = quy.tail(8)
        fig = go.Figure()
        fig.add_bar(x=q["ky"], y=q["dt"] / 1e9, name="Doanh thu (tỷ)", marker_color="#93c5fd")
        fig.add_bar(x=q["ky"], y=q["ln"] / 1e9, name="Lợi nhuận (tỷ)", marker_color="#2563eb")
        fig.update_layout(barmode="group", height=300, margin=dict(l=8, r=8, t=30, b=8), template="plotly_white",
                          title="Doanh thu & lợi nhuận theo quý", legend=dict(orientation="h", y=-0.2))
        st.plotly_chart(fig, width="stretch", key=f"bctc_bd_{noi}_{ma}")
    c1, c2 = st.columns(2)
    phan = c1.selectbox("Báo cáo", list(CB.TEN_PHAN), format_func=CB.TEN_PHAN.get, key=f"bctc_phan_{noi}_{ma}")
    ky = c2.radio("Kỳ", ["Năm", "Quý"], horizontal=True, key=f"bctc_ky_{noi}_{ma}")
    try:
        b = cb_bctc(ma, phan, ky == "Quý")
    except Exception as e:
        loi_nguon(e, "báo cáo tài chính")
        return
    if b.empty:
        st.info("Không có dữ liệu.")
    else:
        st.caption("Đơn vị: tỷ đồng (EPS: đồng)")
        st.dataframe(b.drop(columns="_ma").set_index("Chỉ tiêu").style.format("{:,.1f}", na_rep="–"),
                     width="stretch", height=480)
    try:
        du_lieu_xlsx = cb_excel(ma)
    except Exception:
        return
    st.download_button("⬇ Tải BCTC & chỉ số (Excel)", du_lieu_xlsx, file_name=f"{ma}_tai_chinh.xlsx",
                       width="stretch", key=f"bctc_xlsx_{noi}_{ma}")


def muc_chi_so(ma, noi="tc"):
    try:
        sk, _ = cb_suc_khoe(ma)
        bang_q, moi = cb_chi_so(ma, True)
    except Exception:
        hien_tom_tat_vnd(ma, "cs")
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
    ky = st.radio("Kỳ", ["Quý (4 quý gần nhất)", "Năm"], horizontal=True, key=f"cs_ky_{noi}_{ma}")
    try:
        b = bang_q if ky.startswith("Quý") else cb_chi_so(ma, False)[0]
    except Exception as e:
        loi_nguon(e, "chỉ số theo năm")
        return
    if not b.empty:
        st.caption("Đơn vị: % với ROE, ROA, biên LN, cổ tức, NIM, NPL, CASA; lần (x) với P/E, P/B, nợ.")
        st.dataframe(b.set_index("Chỉ số").style.format("{:,.2f}", na_rep="–"), width="stretch")


# ------------------------------------------------------------------------------------------ giao diện
st.markdown("#### 📈 Dự đoán & khuyến nghị cổ phiếu")

with st.expander("⚙ Cài đặt chung", expanded=False):
    tam_nhan = st.radio("Tầm nắm giữ", list(TAM), horizontal=True)
    von = st.number_input("Số vốn cho mỗi lệnh (đồng)", min_value=1_000_000, value=100_000_000,
                          step=10_000_000, format="%d")
    st.markdown("**Forex / vàng / dầu / crypto** (tính lot theo % rủi ro như cBot)")
    c1, c2, c3 = st.columns(3)
    fx_von = c1.number_input("Tài khoản (USD)", min_value=100.0, value=10_000.0, step=500.0, key="fx_von")
    fx_rr = c2.number_input("Rủi ro mỗi lệnh (%)", min_value=0.1, max_value=10.0, value=1.0, step=0.1, key="fx_rr")
    fx_max = c3.number_input("Rủi ro tối đa ($, 0 = không giới hạn)", min_value=0.0, value=0.0, step=10.0,
                             key="fx_max")
tam = TAM[tam_nhan]

mac_dinh = du_lieu.doc_danh_sach(HERE / "ma.txt")

def trang_bang_day_du():
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
            muc = st.multiselect("Lọc khuyến nghị", K.MUC[::-1], default=["Mua", "Gần đủ điều kiện"])
            b = b[b["Khuyến nghị"].isin(muc)] if not b.empty else b
            dem = b["Khuyến nghị"].value_counts() if not b.empty else {}
            for col, m in zip(st.columns(3), ["Mua", "Gần đủ điều kiện", "Theo dõi"]):
                col.metric(m, int(dem.get(m, 0)))
            if not b.empty:
                cot = [c for c in ["Mã", "Ngành", "Khuyến nghị", "Giá", "Vùng mua", "Giá mua", "Cắt lỗ", "Chốt lời",
                                   "R:R", "% lãi", "Dự kiến chốt lời", "Số phiên dự kiến", "Tiền lãi", "Tiền lỗ", "Số CP",
                                   "Sức khỏe", "P/E", "ROE %",
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
            st.warning("Kiểm định 20 năm (891 mã): tín hiệu đỉnh KHÔNG dự báo được giá giảm một cách ổn định – "
                       "chỉ dùng để tham khảo, không nên bán chỉ vì tín hiệu này.")
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
                    muc_chi_so(kq.ma, "kn")
                chi_tiet(kq, None, "khuyen_nghi")

@st.cache_data(ttl=3600, show_spinner=False)
def gia_ngay(ma):
    return du_lieu.tai(ma, "D")


def tim_ngay():
    return LS.ds_ngay(BAO_CAO / "lich_su")


def trang_theo_ngay():
    ngay_co = tim_ngay()
    if not ngay_co:
        st.info("Chưa có bản khuyến nghị nào được lưu. Mỗi lần quét toàn thị trường (lịch GitHub hằng ngày sau 15h, "
                "hoặc nút Quét ở tab Khuyến nghị) sẽ lưu một bản theo ngày.")
    else:
        xem_ngay = st.radio("Xem", ["📜 Lịch sử khuyến nghị", "🔁 Thay đổi so với phiên trước", "🗓 Lịch sắp tới"],
                            horizontal=True, key="xem_ngay", label_visibility="collapsed")
        if xem_ngay.startswith("📜"):
            ngay = st.selectbox("Ngày", ngay_co, format_func=lambda d: pd.Timestamp(d).strftime("%d/%m/%Y (%A)")
                                .replace("Monday", "Thứ 2").replace("Tuesday", "Thứ 3").replace("Wednesday", "Thứ 4")
                                .replace("Thursday", "Thứ 5").replace("Friday", "Thứ 6").replace("Saturday", "Thứ 7")
                                .replace("Sunday", "CN"), key="ls_ngay")
            ban = LS.doc_ngay(ngay, BAO_CAO / "lich_su")
            st.caption(f"Bản quét lúc {ban.get('luc')} · tầm {'ngắn hạn (D)' if tam == 'D' else 'trung hạn (W)'} "
                       "(đổi ở ⚙ Cài đặt chung)")
            loai = st.radio("Danh sách", ["Nên mua", "Bán ở đỉnh"], horizontal=True, key="ls_loai")
            with st.spinner("Đang tính hiệu quả đến nay…"):
                if loai == "Nên mua":
                    b = LS.hieu_qua_mua(ban.get(f"mua_{tam}", []), ngay, gia_ngay)
                else:
                    b = LS.hieu_qua_ban(ban.get(f"ban_{tam}", []), ngay, gia_ngay)
            if b.empty:
                st.info("Ngày này không có mã nào trong danh sách.")
            else:
                if loai == "Nên mua":
                    dem = b["Trạng thái"].value_counts()
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Đã chạm chốt lời", int(dem.get("Đã chạm chốt lời", 0)))
                    c2.metric("Đã cắt lỗ", int(dem.get("Đã cắt lỗ", 0)))
                    c3.metric("Đang giữ", int(dem.get("Đang giữ", 0)))
                    c4.metric("Chưa khớp", int(sum(v for k, v in dem.items() if k.startswith("Chưa"))))
                    cot = [c for c in ["Mã", "Khuyến nghị", "Trạng thái", "Lãi/lỗ %", "Giá", "Giá mua", "Cắt lỗ",
                                       "Chốt lời", "Dự kiến chốt lời", "Ngày khớp", "Ngày đóng", "Ngành"] if c in b]
                else:
                    cot = [c for c in ["Mã", "Tín hiệu", "Số dấu hiệu", "Giá", "Thay đổi từ hôm đó %", "Đánh giá",
                                       "Vùng bán", "Ngành"] if c in b]

                def mau_lai(v):
                    return "" if v is None or pd.isna(v) else ("color:#16a34a" if v > 0 else "color:#dc2626")
                cot_lai = [c for c in ("Lãi/lỗ %", "Thay đổi từ hôm đó %") if c in cot]
                st.dataframe(b[cot].style.map(mau_lai, subset=cot_lai).format(
                    {"Giá": "{:,.0f}", "Giá mua": "{:,.0f}", "Cắt lỗ": "{:,.0f}", "Chốt lời": "{:,.0f}",
                     "Lãi/lỗ %": "{:+.1f}%", "Thay đổi từ hôm đó %": "{:+.1f}%"}, na_rep="–"),
                    hide_index=True, width="stretch", height=480)
        elif xem_ngay.startswith("🔁"):
            if len(ngay_co) < 2:
                st.info(f"Mới có 1 bản (ngày {pd.Timestamp(ngay_co[0]):%d/%m/%Y}). Cần ít nhất 2 ngày để so sánh.")
            else:
                c1, c2 = st.columns(2)
                a = c1.selectbox("Ngày", ngay_co, index=0, key="ss_a")
                bb = c2.selectbox("So với", ngay_co, index=1, key="ss_b")
                ss = LS.so_sanh(LS.doc_ngay(a, BAO_CAO / "lich_su"), LS.doc_ngay(bb, BAO_CAO / "lich_su"), tam)
                for ten, k in (("Mua", "mua"), ("Gần đủ điều kiện", "cho"), ("Bán ở đỉnh", "ban")):
                    x = ss[k]
                    st.markdown(f"##### {ten}")
                    st.markdown("🟢 **Mới vào:** " + (", ".join(f"`{r['Mã']}`" for r in x["moi_vao"]) or "–")
                                + "  \n🔴 **Bị loại:** " + (", ".join(f"`{r['Mã']}`" for r in x["bi_loai"]) or "–")
                                + f"  \n⚪ Giữ nguyên: {len(x['giu_nguyen'])} mã")
        else:
            moi = LS.doc_ngay(ngay_co[0], BAO_CAO / "lich_su")
            dm_ma = []
            if "dm" in st.session_state:
                dm_ma = [str(m).strip().upper() for m in st.session_state["dm"].get("Mã", []) if str(m).strip()]
            mua = [r for r in moi.get(f"mua_{tam}", []) if (r.get("Hạng") or 0) >= 3]
            ds = dm_ma + [m for m in mac_dinh if du_lieu.phan_loai(m)[0] == "vn" and m not in du_lieu.CHI_SO_VN] \
                + [r["Mã"] for r in mua]
            so_ngay = st.slider("Trong bao nhiêu ngày tới", 7, 90, 30, key="lich_ngay")
            with st.spinner("Đang lấy lịch sự kiện…"):
                lich = LS.lich_sap_toi(ds, mua, so_ngay)
            st.caption("Gồm: cổ tức, ĐHCĐ, phát hành… của các mã đang giữ / theo dõi / nên mua, và ngày dự kiến chốt lời.")
            if lich.empty:
                st.info("Không có sự kiện nào trong khoảng này.")
            else:
                st.dataframe(lich, hide_index=True, width="stretch", height=480)

def trang_bo_loc():
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

def trang_tin():
    nhom = st.radio("Nhóm tin", list(TT.NHOM) + ["Chủ đề vĩ mô"], horizontal=True, key="tin_nhom")
    if nhom == "Chủ đề vĩ mô":
        cd = st.radio("Chủ đề", list(TT.CHU_DE), horizontal=True, key="tin_cd")
        with st.spinner("Đang tìm tin…"):
            ds_cd = tin_chu_de(cd)
        st.caption(f"{len(ds_cd)} tin mới nhất về “{cd}” từ nhiều báo (Google News).")
        hien_tin(ds_cd, 40)
    else:
        c1, c2 = st.columns(2)
        ds_nguon = list(TT.NHOM[nhom])
        nguon = c1.multiselect("Nguồn", ds_nguon, default=ds_nguon, key=f"tin_nguon_{nhom}")
        danh_gia = c2.multiselect("Đánh giá", ["Tích cực", "Tiêu cực", "Trung tính"],
                                  default=["Tích cực", "Tiêu cực", "Trung tính"], key="tin_dg")
        tu_khoa = st.text_input("Tìm theo từ khóa hoặc mã (VD: HPG, lãi suất, ngân hàng)", key="tin_tk")
        chi_co_ma = st.checkbox("Chỉ tin có nhắc tới mã cổ phiếu", key="tin_ma")
        if st.button("🔄 Làm mới tin", key="tin_lm"):
            tin_cho.clear()
        with st.spinner("Đang tải tin…"):
            ds_tin = tin_cho(tuple(nguon), nhom)
        tk = tu_khoa.strip()
        loc = [t for t in ds_tin if t.nhan in danh_gia and (not chi_co_ma or t.ma)
               and (not tk or tk.lower() in t.tieu_de.lower() or tk.upper() in t.ma)]
        st.caption(f"{len(loc)}/{len(ds_tin)} tin · tự làm mới mỗi 15 phút · nhãn đánh giá tự động theo từ khóa"
                   + (" (tin tiếng Anh dùng bộ từ khóa tiếng Anh)" if nhom == "Kinh tế thế giới" else ""))
        hien_tin(loc, 80)

def trang_danh_muc():
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
        con_lai = ""
        if kn and kn.chot_loi1 and v["gia"] and v["gia"] < kn.chot_loi1 and kq.frames.get(tam) is not None:
            try:
                kqk = next(x for x in kq.khung if x.khung == tam)
                tg = K.du_kien_thoi_gian(kq.frames[tam], kqk, v["gia"], kn.chot_loi1)
                if tg.thuong is not None:
                    d = tg.ngay(tg.thuong)
                    con_lai = f"~{tg.phien(tg.thuong)} phiên ({d:%d/%m})" if d is not None else ""
            except Exception:
                pass
        elif kn and kn.chot_loi1 and v["gia"] and v["gia"] >= kn.chot_loi1:
            con_lai = "Đã tới vùng chốt lời"
        rows.append({"Mã": m, "Dự kiến chốt lời": con_lai, "Giá mua": r["Giá mua"], "Giá hiện tại": v["gia"],
                     "Số lượng": r["Số lượng"],
                     "Lãi/lỗ": v["lai"], "%": v["pct"] * 100 if v["pct"] is not None else None,
                     "Gợi ý": v["goi_y"], "Vì sao": v.get("vi_sao", ""), "Tín hiệu đỉnh": dinh.muc if dinh else "–",
                     "Giá bán đề xuất": v["gia_ban"], "Lãi nếu bán": v["lai_neu_ban"],
                     "Cắt lỗ động": v["cat_lo"], "Chốt lời": kn.chot_loi1 if kn else None})
    if rows:
        c1, c2 = st.columns(2)
        c1.metric("Tổng vốn", tien(tong_von))
        c2.metric("Lãi/lỗ (sau phí, thuế)", tien(tong_lai), f"{tong_lai / tong_von:+.1%}" if tong_von else None)
        def mau_lai(v):
            return "" if v is None or pd.isna(v) else ("color:#16a34a" if v > 0 else "color:#dc2626")
        for r in rows:
            mau_r = "#15803d" if r["Gợi ý"] == "Giữ" else "#dc2626" if any(
                x in r["Gợi ý"] for x in ("Cắt lỗ", "Bán")) else "#d97706"
            ban = [f"cắt lỗ nếu thủng **{gd(r['Cắt lỗ động'])}**" if r.get("Cắt lỗ động") else "",
                   f"chốt lời tại **{gd(r['Chốt lời'])}**" if r.get("Chốt lời") else "",
                   f"bán ở đỉnh quanh **{gd(r['Giá bán đề xuất'])}**" if r.get("Giá bán đề xuất") else ""]
            st.markdown(f"<span style='color:{mau_r};font-weight:700'>{r['Mã']}: {r['Gợi ý'].upper()}</span> · "
                        f"giá {gd(r['Giá hiện tại'])} · lãi/lỗ {trieu(r['Lãi/lỗ'])} "
                        f"({pt(r['%'] / 100 if r['%'] is not None else None)})", unsafe_allow_html=True)
            st.markdown("Kế hoạch: " + ", ".join(x for x in ban if x) + (f" · dự kiến {r['Dự kiến chốt lời']}"
                        if r.get("Dự kiến chốt lời") else "") + f"  \nVì sao: {r['Vì sao']}")
        st.dataframe(pd.DataFrame(rows).style.map(mau_lai, subset=["Lãi/lỗ", "%"]).format(
            {"Giá mua": "{:,.0f}", "Giá hiện tại": "{:,.0f}", "Số lượng": "{:,.0f}", "Lãi/lỗ": "{:,.0f}",
             "%": "{:+.1f}%", "Cắt lỗ động": "{:,.0f}", "Chốt lời": "{:,.0f}", "Giá bán đề xuất": "{:,.0f}",
             "Lãi nếu bán": "{:,.0f}"}, na_rep="–"),
            hide_index=True, width="stretch")
        if not st.toggle("📰 Xem tin mới của các mã đang giữ", key="dm_tin"):
            return
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

def trang_theo_doi():
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


# ------------------------------------------------------------------------------------------ kết luận rõ ràng
# Kiểm định toàn thị trường (khuyen_nghi.py, README): 2020–2026, 2.245 lệnh "Mua"
KD_LENH, KD_THANG, KD_LAI, KD_NGAU_NHIEN = 2245, 0.44, 0.036, 0.023
KET_LUAN = {  # mức khuyến nghị → (chữ to, màu, câu hành động)
    "Mua": ("NÊN MUA", "#15803d"),
    "Gần đủ điều kiện": ("CHỜ – SẮP ĐỦ ĐIỀU KIỆN MUA", "#d97706"),
    "Theo dõi": ("CHƯA NÊN MUA – CHỈ THEO DÕI", "#64748b"),
    "Không mua": ("KHÔNG MUA", "#dc2626"),
}


@st.cache_data(ttl=1800, show_spinner=False)
def do_tin_cay(ma: str) -> dict:
    """Các lần công cụ báo Mua chính mã này trong ~2 năm và kết quả (theo đúng quy tắc vào/ra lệnh)."""
    ds = gv_goi(ma).get("tin_hieu") or []
    xong = [x for x in ds if x["ket_qua"] != "Đang giữ"]
    lai = [x["lai_pct"] for x in xong if x["lai_pct"] is not None]
    return {"so": len(xong), "thang": sum(x > 0 for x in lai), "tb": sum(lai) / len(lai) if lai else None,
            "dang_giu": len(ds) - len(xong), "ds": ds}


def cau_tin_cay(tc: dict | None) -> str:
    so = lambda x: f"{x:+.1%}".replace(".", ",")  # noqa: E731
    chung = (f"Kiểm định toàn thị trường 2020–2026 ({KD_LENH:,} lệnh".replace(",", ".")
             + f"): lệnh Mua lãi {KD_THANG:.0%} số lần, TB {so(KD_LAI)}/lệnh; mua ngẫu nhiên giữ 60 phiên "
             f"{so(KD_NGAU_NHIEN)} → **chưa tốt hơn mua ngẫu nhiên một cách chắc chắn**, chỉ nên tham khảo.")
    if tc is None:
        return chung
    if not tc["so"]:
        rieng = "Mã này chưa có lần báo Mua nào (đã đóng lệnh) trong ~2 năm để đánh giá riêng."
    else:
        rieng = (f"Riêng mã này ~2 năm: báo Mua {tc['so']} lần, **lãi {tc['thang']}/{tc['so']}**, "
                 f"TB {tc['tb']:+.1f}%/lệnh.")
    return rieng + "  \n" + chung


def trieu(x):
    """Số tiền gọn: 19,2 triệu / 1,25 tỷ."""
    if x is None or pd.isna(x):
        return "–"
    a = abs(x)
    t = f"{x / 1e9:,.2f} tỷ" if a >= 1e9 else f"{x / 1e6:,.1f} triệu" if a >= 1e6 else f"{x:,.0f} đ"
    return t.replace(",", "X").replace(".", ",").replace("X", ".")


def pt(x):
    return "–" if x is None else f"{x:+.1%}".replace(".", ",")


def gd(x):
    return "–" if x is None or pd.isna(x) else f"{x:,.0f}".replace(",", ".")


@st.cache_data(ttl=1800, show_spinner=False)
def diem_mh(ma: str):
    try:
        return MH.diem_mo_hinh(du_lieu.tai(ma, "D"))
    except Exception:
        return None


def cau_mo_hinh(m: dict | None) -> str:
    if not m:
        return ""
    return (f"🤖 Điểm mô hình (thử nghiệm): **{m['diem']:.0f}/100** (nhóm {m['nhom']}/10) – lịch sử nhóm này: "
            f"vượt TB thị trường {pt(m['vuot_tb_20'])}/20 phiên, {m['ti_le_thang_20']:.0%} số lần vượt. "
            "Độ tin cậy thấp, chỉ tham khảo.")


def the_ke_hoach(kq, kn, gt: dict, gon: bool = False):
    """Kế hoạch: điểm mua / cắt lỗ / chốt lời (giá, %, tiền), ngày dự kiến, lãi kỳ vọng và VÌ SAO."""
    vao = gt["vao_lenh"]
    nen = "#ecfdf5" if vao else "#f8fafc"
    vien = "#15803d" if vao else "#94a3b8"
    tien = gt.get("so_cp")
    vung = f" (vùng đẹp {gd(gt['vung'][0])}–{gd(gt['vung'][1])})" if gt.get("vung") else ""
    hang = [
        ("🟦 Điểm mua", f"{gd(gt['gia_mua'])}{vung}", "",
         f"{gd(gt['so_cp'])} CP = {trieu(gt['tien_mua'])}" if tien else "", gt["vi_sao_mua"]),
        ("🟥 Cắt lỗ", gd(gt["cat_lo"]), pt(gt["lo_pct"]), trieu(gt.get("tien_lo")) if tien else "",
         gt["vi_sao_cat_lo"]),
        ("🟩 Chốt lời", gd(gt["chot_loi"]), pt(gt["lai_pct"]),
         ("+" + trieu(gt.get("tien_lai"))) if tien else "", gt["vi_sao_chot_loi"]),
    ]
    html = (f"<div style='border:2px solid {vien};background:{nen};border-radius:12px;padding:10px 12px;margin:6px 0'>"
            f"<div style='font-weight:700;color:{vien}'>{'✅ ' if vao else '⏸ '}KẾ HOẠCH: {gt['trang_thai']}</div>"
            f"<div style='font-size:13px;color:#475569;margin-bottom:6px'>{gt['dieu_kien']}</div>")
    for ten, gia, p_, tien_, ly in hang:
        html += (f"<div style='padding:4px 0;border-top:1px solid #e2e8f0'><b>{ten}: {gia}</b>"
                 + (f" <b>({p_})</b>" if p_ else "") + (f" · {tien_}" if tien_ else "")
                 + ("" if gon else f"<div style='font-size:12.5px;color:#64748b'>{ly}</div>") + "</div>")
    if gt.get("ngay_du_kien") is not None:
        kh = (f" (sớm {gt['ngay_som']:%d/%m} – muộn {gt['ngay_muon']:%d/%m/%Y})"
              if gt.get("ngay_som") is not None and gt.get("ngay_muon") is not None else "")
        html += (f"<div style='padding:4px 0;border-top:1px solid #e2e8f0'>📅 Dự kiến chạm chốt lời: "
                 f"<b>{gt['ngay_du_kien']:%d/%m/%Y}</b>{kh}" + (" – nếu vào lệnh" if not vao else "") + "</div>")
    if tien:
        html += (f"<div style='padding:4px 0;border-top:1px solid #e2e8f0'>💰 Với vốn {trieu(von)}: đúng → "
                 f"<b style='color:#15803d'>+{trieu(gt['tien_lai'])}</b> ({pt(gt['pct_lai_rong'])}), sai → "
                 f"<b style='color:#dc2626'>{trieu(gt['tien_lo'])}</b> ({pt(gt['pct_lo_rong'])}) – đã trừ phí, thuế."
                 + (f" Trung bình kỳ vọng theo kiểm định: <b>≈ +{trieu(gt['tien_ky_vong'])}/lệnh</b> "
                    f"({pt(gt['ky_vong_pct'])})." if vao else " Lãi kỳ vọng chỉ tính khi tín hiệu đủ điều kiện.")
                 + "</div>")
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)
    if not gon:
        st.markdown("**❓ Vì sao**  \n" + "  \n".join(gt["vi_sao"]))
        st.caption(gt["ky_vong"])


def the_ket_luan(kq, kn, dinh, tc: dict | None, gt: dict, mh: dict | None = None):
    """Thẻ kết luận một mã: NÊN MUA / CHỜ / KHÔNG MUA + kế hoạch rõ ràng + vì sao + độ tin cậy."""
    chu, mau = KET_LUAN.get(kn.muc, (kn.muc.upper(), "#64748b"))
    st.markdown(
        f"<div style='padding:14px 16px;border-radius:14px;background:{mau};color:white'>"
        f"<div style='font-size:14px;opacity:.9'>{kq.ma} · giá {gd(kq.chinh.gia)} · "
        f"{'ngắn hạn 1–3 tháng' if kn.tam == 'D' else 'trung hạn 3–9 tháng'} · điểm {kn.diem:+.0f}</div>"
        f"<div style='font-size:28px;font-weight:800;line-height:1.2'>{chu}</div></div>", unsafe_allow_html=True)
    the_ke_hoach(kq, kn, gt)
    if dinh is not None and dinh.muc in ("Bán mạnh", "Chốt lời dần"):
        vb = f" quanh {gd(dinh.vung_ban[0])}–{gd(dinh.vung_ban[1])}" if dinh.vung_ban else ""
        st.warning(f"Nếu đang giữ: có tín hiệu đỉnh (**{dinh.muc}**){vb} – độ tin cậy thấp theo kiểm định.")
    if mh:
        st.markdown(cau_mo_hinh(mh))
    st.caption(cau_tin_cay(tc).replace("**", ""))


def the_xu_huong(kq):
    """Chỉ số / forex / cổ phiếu nước ngoài: kết luận theo xu hướng."""
    mau = MAU[kq.xu_huong]
    chu = {1: "XU HƯỚNG TĂNG", -1: "XU HƯỚNG GIẢM", 0: "ĐI NGANG – CHƯA RÕ"}[kq.xu_huong]
    st.markdown(f"<div style='padding:14px 16px;border-radius:14px;background:{mau};color:white'>"
                f"<div style='font-size:14px;opacity:.9'>{kq.ma} · điểm {kq.diem:+.0f}/100</div>"
                f"<div style='font-size:28px;font-weight:800'>{MUI_TEN[kq.xu_huong]} {chu}</div></div>",
                unsafe_allow_html=True)
    kh = bao_cao.ke_hoach(kq)
    if kh.get("sl") and kh.get("tp1"):
        st.markdown(f"Giá {kq.chinh.gia:,.4g} · cắt lỗ **{kh['sl']:,.4g}** · chốt lời **{kh['tp1']:,.4g}** "
                    f"(kế hoạch Fibonacci khung {kq.chinh.khung}, chưa kiểm định).")
    st.caption("Chỉ dự báo xu hướng; khuyến nghị mua kèm kiểm định chỉ áp dụng cho cổ phiếu Việt Nam.")


def so_fx(x, ts):
    """Hiện giá forex đủ số lẻ theo pip (EURUSD 5 số, USDJPY 3 số, vàng 2 số)."""
    nd = max(0, int(round(-math.log10(ts.pip))) + 1) if ts.pip < 1 else 2
    return f"{x:,.{nd}f}"


def the_forex(kq):
    """Forex / vàng / dầu / crypto: lệnh Buy hoặc Sell, pip, lot theo % rủi ro (công thức cBot)."""
    try:
        k = FX.ke_hoach_fx(kq, fx_von, fx_rr, fx_max)
    except Exception as e:
        st.warning(f"Chưa tính được kế hoạch forex: {str(e)[:150]}")
        the_xu_huong(kq)
        return
    if not k.get("huong"):
        st.markdown(f"<div style='padding:14px 16px;border-radius:14px;background:#64748b;color:white'>"
                    f"<div style='font-size:14px;opacity:.9'>{kq.ma} · khung {k.get('khung', '')}</div>"
                    f"<div style='font-size:28px;font-weight:800'>ĐỨNG NGOÀI – CHƯA RÕ HƯỚNG</div></div>",
                    unsafe_allow_html=True)
        st.markdown(k["ly_do"])
        return
    ts = k["thong_so"]
    mua = k["huong"].startswith("MUA")
    mau = "#15803d" if mua else "#dc2626"
    kl = k["khoi_luong"]
    don_vi = {"vang": "oz", "bac": "oz", "dau": "thùng", "crypto": "coin"}.get(ts.loai, "đơn vị")
    st.markdown(
        f"<div style='padding:14px 16px;border-radius:14px;background:{mau};color:white'>"
        f"<div style='font-size:14px;opacity:.9'>{kq.ma} · khung {k['khung']} · giá {so_fx(k['gia'], ts)}</div>"
        f"<div style='font-size:28px;font-weight:800'>{'▲' if mua else '▼'} {k['huong']}</div></div>"
        f"<div style='border:2px solid {mau};border-radius:12px;padding:10px 12px;margin:6px 0'>"
        f"<div style='padding:4px 0'><b>🟦 Vào lệnh: {so_fx(k['vao'], ts)}</b> · <b>{kl['lot']:.2f} lot</b> "
        f"({kl['don_vi']:,.0f} {don_vi}) · 1 pip = {k['gia_tri_pip']:,.2f} USD</div>"
        f"<div style='padding:4px 0;border-top:1px solid #e2e8f0'><b>🟥 Cắt lỗ: {so_fx(k['cat_lo'], ts)}</b> "
        f"({k['sl_pip']:,.1f} pip) → <b style='color:#dc2626'>{k['lo_usd']:,.2f} USD</b> "
        f"({k['lo_usd'] / fx_von:.2%} tài khoản)</div>"
        f"<div style='padding:4px 0;border-top:1px solid #e2e8f0'><b>🟩 Chốt lời: {so_fx(k['chot_loi'], ts)}</b> "
        f"({k['tp_pip']:,.1f} pip) → <b style='color:#15803d'>+{k['lai_usd']:,.2f} USD</b> "
        f"({k['lai_usd'] / fx_von:+.2%}) · R:R 1:{k['rr']:g}</div></div>", unsafe_allow_html=True)
    st.markdown(
        f"**Cách tính lot (giống cBot):** tiền rủi ro = {fx_von:,.0f} × {fx_rr:g}% = **{kl['tien_rui_ro']:,.2f} USD**"
        f"{f' (trần {fx_max:,.0f} USD)' if fx_max else ''}; lot = {kl['tien_rui_ro']:,.2f} ÷ ({kl['sl_pip']:,.1f} pip × "
        f"{kl['gia_tri_pip_lot']:,.2f} USD/pip/lot) = {kl['lot_tho']:.4f} → làm tròn xuống **{kl['lot']:.2f} lot**. "
        f"Rủi ro thực {kl['rui_ro_thuc']:,.2f} USD ({kl['rui_ro_thuc_pct']:.2%}).")
    if kl["canh_bao"]:
        st.warning(kl["canh_bao"])
    st.markdown("**❓ Vì sao:** " + k["ly_do"])
    st.caption("Forex khác cổ phiếu VN: có cả lệnh Bán (Sell), tính bằng pip/lot, không thuế bán, chi phí là spread/"
               "swap (chưa trừ). 1 lot = 100.000 đơn vị tiền (vàng 100 oz, bạc 5.000 oz, dầu 1.000 thùng). "
               "Giá trị pip là ước tính theo tỷ giá Yahoo – sàn của bạn có thể khác chút.")


def la_co_phieu_vn(kq):
    return kq.khung and kq.loai == "vn" and kq.ma not in du_lieu.CHI_SO_VN and tam in kq.frames


def xem_ma(ma: str, noi: str):
    """Toàn bộ thông tin một mã: kết luận → biểu đồ → doanh nghiệp → tin → chi tiết."""
    with st.spinner(f"Đang phân tích {ma}…"):
        kq, _, tl = phan_tich(ma, False)
    if not kq.khung:
        st.markdown(f"#### {ma}: Không có dữ liệu")
        for g in kq.ghi_chu[:3]:
            st.warning(g)
        return
    if la_co_phieu_vn(kq):
        kn = K.khuyen_nghi(kq, tam)
        try:
            CB.dieu_chinh_khuyen_nghi(kn, CB.tom_tat_co_ban(kq.ma, kq.frames.get("D")))
        except Exception:
            pass
        dinh = K.tin_hieu_dinh(kq, tam)
        the_ket_luan(kq, kn, dinh, None, K.giai_thich(kq, kn, von), diem_mh(kq.ma))
        if st.toggle("🔎 Kiểm tra các lần công cụ báo Mua mã này trước đây (~5 giây)", key=f"tc_{noi}_{kq.ma}"):
            try:
                with st.spinner("Đang mô phỏng lại các lần báo Mua trong ~2 năm…"):
                    tc = do_tin_cay(kq.ma)
            except Exception as e:
                tc = None
                st.info(f"Chưa kiểm tra được: {str(e)[:120]}")
            if tc is not None:
                st.markdown(cau_tin_cay(tc).split("  \n")[0])
                if tc["ds"]:
                    st.dataframe(pd.DataFrame([{"Ngày mua": pd.Timestamp(x["t_mua"], unit="s").strftime("%d/%m/%Y"),
                                                "Giá mua": x["gia_mua"], "Kết quả": x["ket_qua"],
                                                "Ngày ra": pd.Timestamp(x["t_ra"], unit="s").strftime("%d/%m/%Y"),
                                                "Lãi %": x["lai_pct"]} for x in tc["ds"]]).style.format(
                        {"Giá mua": "{:,.0f}", "Lãi %": "{:+.1f}%"}), hide_index=True, width="stretch")
        with st.expander("📋 Thêm: chốt lời từng phần, tín hiệu đỉnh chi tiết"):
            the_khuyen_nghi(kn, von)
            the_tin_hieu_dinh(dinh)
        # chỉ tải phần đang chọn (st.tabs chạy hết mọi thẻ → chậm)
        muc = st.radio("Xem thêm", ["📈 Biểu đồ", "🏢 Doanh nghiệp", "📰 Tin tức", "🔬 Chi tiết chỉ báo"],
                       horizontal=True, key=f"muc_{noi}_{kq.ma}", label_visibility="collapsed")
        if muc == "📈 Biểu đồ":
            bieu_do_plotly(kq, noi)
        elif muc == "🏢 Doanh nghiệp":
            muc_doanh_nghiep(kq.ma)
            st.markdown("---")
            muc_chi_so(kq.ma, noi)
            with st.expander("📊 Báo cáo tài chính đầy đủ"):
                muc_tai_chinh(kq.ma, noi)
        elif muc == "📰 Tin tức":
            try:
                ten = (cb_ho_so(kq.ma)[0] or {}).get("ten_ngan")
            except Exception:
                ten = None
            muc_tin_tuc(kq.ma, ten)
        else:
            chi_tiet(kq, tl, noi + "_kt", dau=False)
    else:
        if kq.loai == "fx":
            the_forex(kq)
        else:
            the_xu_huong(kq)
        khung_dinh = "4H" if kq.loai == "fx" else tam
        if khung_dinh in kq.frames:
            with st.expander("Tín hiệu đỉnh"):
                the_tin_hieu_dinh(K.tin_hieu_dinh(kq, khung_dinh, loai=kq.loai))
        chi_tiet(kq, tl, noi, dau=False)


def tai_song_song(ds: tuple):
    """Tải giá nhiều mã cùng lúc (mỗi mã là 1 lần gọi mạng) – nhanh hơn tải lần lượt."""
    from concurrent.futures import ThreadPoolExecutor

    def tai(m):
        try:
            du_lieu.tai(m, "D")
        except Exception:
            pass
    with ThreadPoolExecutor(6) as ex:
        list(ex.map(tai, ds))


@st.cache_data(ttl=1800, show_spinner=False)
def thi_truong_chung():
    kq, _, _ = phan_tich_ma("VNINDEX")
    return kq


def trang_hom_nay():
    kho = kho_thi_truong()
    doc_file_thi_truong(kho)
    # 1) Thị trường chung
    try:
        vni = thi_truong_chung()
    except Exception:
        vni = None
    if vni is not None and vni.khung:
        loi_khuyen = {1: "có thể giải ngân dần vào mã tốt", 0: "giải ngân thận trọng, ưu tiên mã thật mạnh",
                      -1: "nên giữ nhiều tiền mặt, hạn chế mua mới"}[vni.xu_huong]
        st.markdown(f"<div style='padding:10px 14px;border-radius:12px;border:2px solid {MAU[vni.xu_huong]}'>"
                    f"<b>Thị trường (VNINDEX {vni.chinh.gia:,.0f}):</b> "
                    f"<span style='color:{MAU[vni.xu_huong]};font-weight:700'>{MUI_TEN[vni.xu_huong]} {vni.nhan.upper()}"
                    f"</span> → {loi_khuyen}.</div>", unsafe_allow_html=True)
    b = kho.get(tam)
    if b is None or b.empty:
        st.info("Chưa có bảng khuyến nghị – mở mục **Cập nhật dữ liệu** bên dưới và bấm Quét.")
    else:
        tk = kho["thong_ke"] or {}
        b = b[b["GTGD (tỷ)"].fillna(0) >= 1]
        hang = {m: i for i, m in enumerate(K.MUC)}
        b = b.assign(_h=b["Khuyến nghị"].map(hang)).sort_values(["_h", "Điểm"], ascending=False)
        mua = b[b["Khuyến nghị"] == "Mua"]
        the = []
        ung_vien = b.head(max(5, len(mua)))
        tai_song_song(tuple(ung_vien["Mã"]))
        for _, r in ung_vien.iterrows():
            try:      # phân tích lại theo giá mới nhất để thẻ khớp với trang Tra cứu
                kq_r, _, _ = phan_tich(r["Mã"], False)
                kn_r = K.khuyen_nghi(kq_r, tam)
                the.append((r, kq_r, kn_r, K.giai_thich(kq_r, kn_r, von), kn_r.muc, kn_r.gia))
            except Exception:
                the.append((r, None, None, None, r["Khuyến nghị"], r["Giá"]))
        the.sort(key=lambda x: -K.MUC.index(x[4]) if x[4] in K.MUC else 0)
        so_mua = sum(x[4] == "Mua" for x in the)
        st.markdown(f"#### 🟢 Nên mua lúc này: {so_mua} mã")
        st.caption(f"Danh sách lấy từ bản quét {kho['luc']} ({tk.get('phan_tich', len(b))} mã đủ thanh khoản), "
                   "kết luận tính lại theo giá mới nhất. "
                   + ("Rất ít mã đủ điều kiện – đó là tín hiệu nên chờ, chưa vội mua." if so_mua < 2 else ""))
        for r, kq_r, kn_r, gt, muc, gia in the:
            chu, mau = KET_LUAN.get(muc, (muc, "#64748b"))
            mh = r.get("Điểm mô hình")
            st.markdown(f"<div style='margin-top:10px;padding:6px 12px;border-radius:10px 10px 0 0;background:{mau};"
                        f"color:white'><b style='font-size:17px'>{r['Mã']}</b> · <b>{chu}</b> · giá {gd(gia)}"
                        f"<span style='font-size:12px;opacity:.9'> · {r.get('Ngành') or ''}"
                        + (f" · 🤖 {mh:.0f}/100" if isinstance(mh, (int, float)) and not pd.isna(mh) else "")
                        + "</span></div>", unsafe_allow_html=True)
            if gt:
                the_ke_hoach(kq_r, kn_r, gt, gon=True)
                ly = [x[2:] for x in gt["vi_sao"][1:] if x.startswith("✔")][:2]
                st.caption(("Vì sao: " + " · ".join(ly)) if ly else gt["dieu_kien"])
            else:
                st.caption(f"Mua {r.get('Vùng mua') or gd(r.get('Giá mua'))} · cắt lỗ {gd(r.get('Cắt lỗ'))} · "
                           f"chốt lời {gd(r.get('Chốt lời'))}")
        st.caption("Luôn hiện 5 mã điểm cao nhất (theo bản quét) kể cả khi chưa đủ điều kiện mua – khi đó kế hoạch ghi "
                   "\"THAM KHẢO – CHƯA VÀO\". 🤖 = điểm mô hình học máy (thử nghiệm). "
                   + cau_tin_cay(None).replace("**", ""))
        ban = kho.get(f"ban_{tam}")
        if ban is not None and not ban.empty:
            manh = ban[ban["Tín hiệu"] == "Bán mạnh"]
            if not manh.empty:
                st.markdown(f"#### 🔴 Nếu đang giữ, cân nhắc chốt lời: {', '.join(manh['Mã'].head(12))}")
                st.caption("Tín hiệu đỉnh – kiểm định cho thấy độ tin cậy thấp, chỉ để tham khảo.")
        chon = st.selectbox("Xem chi tiết mã", [x[0]["Mã"] for x in the], index=None, placeholder="Chọn mã để xem chi tiết",
                            key="hn_chon")
        if chon:
            xem_ma(chon, "hom_nay")
    with st.expander("🔄 Cập nhật dữ liệu (quét lại toàn thị trường)"):
        c1, c2 = st.columns(2)
        san = c1.multiselect("Sàn", ["HSX", "HNX", "UPCOM"], default=["HSX", "HNX", "UPCOM"],
                             format_func=lambda x: du_lieu.SAN[x], key="hn_san")
        gtgd = c2.number_input("GTGD tối thiểu (tỷ đồng/phiên)", min_value=0.0, value=1.0, step=0.5, key="hn_gtgd")
        if st.button("🔄 Quét toàn thị trường (~3–7 phút)", width="stretch", key="hn_quet"):
            quet_ngay(kho, san or ["HSX"], gtgd * 1e9)
            st.rerun()


def trang_tra_cuu():
    with st.form("tra_cuu"):
        ma = st.text_input("Nhập mã (VD: FPT, HPG, VNINDEX, XAUUSD, EURUSD, AAPL)",
                           value=st.session_state.get("ma", "FPT"))
        ok = st.form_submit_button("Phân tích", type="primary", width="stretch")
    if ok:
        st.session_state["ma"] = ma.strip().upper()
    ma = st.session_state.get("ma", "FPT")
    if ma:
        xem_ma(ma, "tra_cuu")


NANG_CAO = {"📋 Bảng khuyến nghị đầy đủ": "trang_bang_day_du", "📅 Khuyến nghị theo ngày": "trang_theo_ngay",
            "🔎 Bộ lọc cơ bản": "trang_bo_loc", "📰 Tin thị trường": "trang_tin"}

t_hn, t_tc, t_dm, t_nc = st.tabs(["🏠 Hôm nay", "🔍 Tra cứu mã", "💼 Danh mục của tôi", "🧰 Nâng cao"])
with t_hn:
    trang_hom_nay()
with t_tc:
    trang_tra_cuu()
with t_dm:
    trang_danh_muc()
    if st.toggle("📋 Phân tích danh sách theo dõi (nhiều mã cùng lúc)", key="td_bat"):
        trang_theo_doi()
with t_nc:
    trang = st.radio("Mục", list(NANG_CAO), horizontal=True, key="nang_cao", label_visibility="collapsed")
    globals()[NANG_CAO[trang]]()

st.divider()
st.caption("⚠ " + bao_cao.CANH_BAO)
