"""Dự đoán xu hướng giá Tăng / Giảm / Đi ngang.

Ví dụ:
  py du_doan.py FPT EURUSD XAUUSD        phân tích các mã, in ra màn hình
  py du_doan.py --tat-ca --bao-cao       phân tích mọi mã trong ma.txt, ghi báo cáo vào bao_cao/
  py du_doan.py --file gia_FPT.csv --ten FPT     dùng file giá tự tải (cột Ngày, Mở, Cao, Thấp, Đóng, KL)
  py du_doan.py --quet-thi-truong              quét toàn bộ HOSE/HNX/UPCoM → khuyến nghị mua, xếp hạng
"""
import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from dudoan import bao_cao, du_lieu, phan_tich  # noqa: E402

TOI = {"D": 5, "4H": 6, "1H": 8, "W": 3, "M": 2, "15m": 8}   # số nến để kiểm tra đúng/sai


def phan_tich_ma(ma: str, df_goc=None, thu_lai: bool = False):
    """Phân tích một mã trên mọi khung. Trả về (KetQua, DataFrame khung chính, kết quả thử lại)."""
    loai, chuan = du_lieu.phan_loai(ma)
    ket_qua, frames, loi = [], {}, []
    for khung in du_lieu.KHUNG[loai]:
        try:
            if df_goc is not None:
                if khung in ("D", "1H", "15m"):
                    df = df_goc
                else:
                    df = du_lieu.resample(df_goc, khung)
            else:
                df = du_lieu.tai(ma, khung)
            frames[khung] = df
            ket_qua.append(phan_tich.phan_tich_khung(df, khung))
        except Exception as e:
            loi.append(f"{khung}: {e}")
    kq = phan_tich.tong_hop(chuan, loai, ket_qua)
    if loi and not ket_qua:
        kq.ghi_chu.extend(loi)
    elif loi:
        kq.ghi_chu.append("Thiếu khung " + ", ".join(x.split(":")[0] for x in loi))
    kq.frames = frames
    df_chinh = frames.get(kq.chinh.khung) if kq.khung else None
    tl = None
    if thu_lai and df_chinh is not None and len(df_chinh) > 120:
        tl = phan_tich.kiem_tra_qua_khu(df_chinh, kq.chinh.khung, toi=TOI.get(kq.chinh.khung, 5))
    return kq, df_chinh, tl


def main(argv=None):
    ap = argparse.ArgumentParser(description="Dự đoán xu hướng giá (Stoch, MACD, MFI, ADX, ICT, SMC)")
    ap.add_argument("ma", nargs="*", help="mã: FPT, VNINDEX, EURUSD, XAUUSD, AAPL, vn:ABC, fx:..., us:...")
    ap.add_argument("--tat-ca", action="store_true", help="dùng danh sách trong ma.txt")
    ap.add_argument("--danh-sach", default=str(HERE / "ma.txt"))
    ap.add_argument("--bao-cao", action="store_true", help="ghi báo cáo HTML/Markdown/Excel")
    ap.add_argument("--thu-muc", default=str(HERE / "bao_cao"))
    ap.add_argument("--thu-lai", action="store_true", help="thử lại tín hiệu trên dữ liệu quá khứ")
    ap.add_argument("--gon", action="store_true", help="chỉ in một dòng mỗi mã")
    ap.add_argument("--file", help="file CSV/Excel giá tự tải")
    ap.add_argument("--ten", help="tên mã cho --file")
    ap.add_argument("--quet-thi-truong", action="store_true", help="quét toàn bộ cổ phiếu VN, xếp hạng khuyến nghị")
    ap.add_argument("--san", default="HSX,HNX,UPCOM", help="sàn cần quét, VD: HSX,HNX")
    ap.add_argument("--gtgd", type=float, default=1.0, help="GTGD tối thiểu (tỷ đồng/phiên)")
    ap.add_argument("--von", type=float, default=100e6, help="số vốn mỗi lệnh để tính lãi (đồng)")
    a = ap.parse_args(argv)

    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    if a.quet_thi_truong:
        return quet_thi_truong(a)

    jobs = []
    if a.file:
        jobs.append((a.ten or Path(a.file).stem.upper(), du_lieu.doc_file(a.file)))
    ds_ma = list(a.ma)
    if a.tat_ca or (not ds_ma and not a.file):
        ds_ma += du_lieu.doc_danh_sach(a.danh_sach)
    jobs += [(m, None) for m in ds_ma]

    ket_qua, du_lieu_ve, thu_lai = [], {}, {}
    for ma, df in jobs:
        try:
            kq, df_chinh, tl = phan_tich_ma(ma, df, thu_lai=a.thu_lai or a.bao_cao)
        except Exception as e:   # một mã lỗi không làm dừng cả danh sách
            print(f"{ma}: lỗi – {e}\n")
            continue
        ket_qua.append(kq)
        du_lieu_ve[kq.ma] = df_chinh
        thu_lai[kq.ma] = tl
        print(bao_cao.van_ban(kq, chi_tiet=not a.gon))
        if tl and tl["ti_le"] is not None:
            print(f"  Thử lại quá khứ: {tl['dung']}/{tl['tin_hieu']} đúng ({tl['ti_le']:.0%})")
        print()

    if a.bao_cao:
        path = bao_cao.ghi(a.thu_muc, ket_qua, du_lieu_ve, thu_lai)
        print(f"Đã ghi báo cáo: {path}")
    print(bao_cao.CANH_BAO)
    return 0 if any(k.khung for k in ket_qua) else 1


def quet_thi_truong(a):
    from dudoan import quet
    print("Đang quét toàn thị trường (vài phút)…")
    kq = quet.quet(san=tuple(x.strip().upper() for x in a.san.split(",")), gtgd_min=a.gtgd * 1e9,
                   tien_trinh=lambda i, n, ma: print(f"  {i}/{n}", flush=True) if i % 200 == 0 else None)
    data = quet.ghi(a.thu_muc, kq, a.von)
    tk = data["thong_ke"]
    print(f"Quét {tk['tong']} mã, phân tích {tk['phan_tich']} mã đủ thanh khoản "
          f"({tk['tang']} tăng, {tk['giam']} giảm).")
    for tam, ten in (("D", "NGẮN HẠN (D)"), ("W", "TRUNG HẠN (W)")):
        top = [x for x in data[tam] if x["Hạng"] >= 3][:15]
        print(f"\n== {ten}: {len([x for x in data[tam] if x['Hạng'] >= 3])} mã nên mua ==")
        for x in top:
            print(f"  {x['Mã']:<4} {x['Khuyến nghị']:<9} giá {x['Giá']:>9,.0f}  mua {x['Giá mua'] or 0:>9,.0f}  "
                  f"cắt lỗ {x['Cắt lỗ'] or 0:>9,.0f}  chốt lời {x['Chốt lời'] or 0:>9,.0f}  "
                  f"lãi {x['% lãi'] or 0:+.1f}%  R:R {x['R:R'] or 0:.1f}")
    print(f"\nĐã ghi: {Path(a.thu_muc) / 'khuyen_nghi.xlsx'}, khuyen_nghi.md")
    print(bao_cao.CANH_BAO)
    return 0


if __name__ == "__main__":
    sys.exit(main())
