"""Cấu hình chung cho test công cụ cổ phiếu: KHÔNG gọi mạng.

Số liệu doanh nghiệp (hồ sơ, BCTC, chỉ số…) lấy từ tests/du_lieu/co_ban_mau.json.gz (FPT, VCB
tải từ Vietcap ngày 19/11/2026). Mã khác coi như không có dữ liệu.
"""
import gzip
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

MAU = json.loads(gzip.decompress((Path(__file__).parent / "du_lieu" / "co_ban_mau.json.gz").read_bytes()))


@pytest.fixture(autouse=True)
def khong_goi_mang(monkeypatch, tmp_path):
    try:
        from dudoan import co_ban
    except Exception:          # thiếu thư viện → các test tự bỏ qua
        yield
        return

    def goi_gia(duong_dan):
        k = re.sub(r"&toDate=\d+", "", duong_dan)
        if k in MAU:
            return MAU[k]
        raise RuntimeError(f"(test) không có dữ liệu mẫu cho {duong_dan}")
    monkeypatch.setattr(co_ban, "_goi", goi_gia)
    monkeypatch.setattr(co_ban, "THU_MUC_CACHE", tmp_path / "cache")
    co_ban._bo_nho.clear()

    from dudoan import tin_tuc
    du_lieu_tin = Path(__file__).parent / "du_lieu"

    def tai_gia(url):
        if "news.google.com" in url:
            return (du_lieu_tin / "rss_google_fpt.xml").read_bytes()
        for ten in ("cafef", "vietstock", "vnexpress"):
            if ten in url:
                return (du_lieu_tin / f"rss_{ten}.xml").read_bytes()
        raise RuntimeError(f"(test) không có tin mẫu cho {url}")
    monkeypatch.setattr(tin_tuc, "_tai", tai_gia)
    yield
    co_ban._bo_nho.clear()
