"""Cấu hình chung cho test công cụ cổ phiếu: KHÔNG gọi mạng.

Số liệu doanh nghiệp (hồ sơ, BCTC, chỉ số…) lấy từ tests/du_lieu/co_ban_mau.json.gz (FPT, VCB
tải từ Vietcap ngày 19/11/2026). Mã khác coi như không có dữ liệu.
"""
import gzip
import json
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
        if duong_dan in MAU:
            return MAU[duong_dan]
        raise RuntimeError(f"(test) không có dữ liệu mẫu cho {duong_dan}")
    monkeypatch.setattr(co_ban, "_goi", goi_gia)
    monkeypatch.setattr(co_ban, "THU_MUC_CACHE", tmp_path / "cache")
    co_ban._bo_nho.clear()
    yield
    co_ban._bo_nho.clear()
