import pikepdf
import pytest

from app.core import pages
from app.core.compress import CompressOptions, compress_pdf
from app.core.files import human_size, unique_path
from app.core.ghostscript import find_ghostscript
from app.core.ranges import RangeError, pages_in, parse_ranges
from tests.conftest import page_widths

needs_gs = pytest.mark.skipif(find_ghostscript() is None, reason="Ghostscript not installed")


# ---------- ranges ----------
def test_parse_ranges_mixed():
    assert parse_ranges("1-3, 5, 9-end", 10) == [(1, 3), (5, 5), (9, 10)]
    assert parse_ranges(" last ", 4) == [(4, 4)]
    assert pages_in([(1, 2), (2, 3)]) == {1, 2, 3}


@pytest.mark.parametrize("text,msg", [
    ("", "at least one"), ("0", "out of range"), ("11", "out of range"),
    ("5-2", "backwards"), ("a-3", "not a page number"),
])
def test_parse_ranges_errors(text, msg):
    with pytest.raises(RangeError, match=msg):
        parse_ranges(text, 10)


# ---------- files ----------
def test_unique_path_never_overwrites(tmp_path):
    (tmp_path / "a.pdf").write_bytes(b"x")
    (tmp_path / "a (2).pdf").write_bytes(b"x")
    assert unique_path(tmp_path, "a").name == "a (3).pdf"


def test_human_size():
    assert human_size(512) == "512 B"
    assert human_size(1536) == "1.5 KB"
    assert human_size(5 * 1024 * 1024) == "5.0 MB"


# ---------- page tools ----------
def test_merge_order(ten_pages, tmp_path):
    out = pages.merge([ten_pages, ten_pages], tmp_path / "m.pdf")
    assert page_widths(out) == list(range(10)) * 2


def test_split_every(ten_pages, tmp_path):
    outs = pages.split(ten_pages, tmp_path / "o", "every", every=4)
    assert [len(page_widths(o)) for o in outs] == [4, 4, 2]
    assert outs[2].name == "ten_p9-10.pdf"


def test_split_ranges_and_extract(ten_pages, tmp_path):
    outs = pages.split(ten_pages, tmp_path / "o", "ranges", ranges_text="2-3, 7")
    assert [page_widths(o) for o in outs] == [[1, 2], [6]]
    one = pages.split(ten_pages, tmp_path / "o", "ranges", ranges_text="2-3, 7", single_file=True)
    assert page_widths(one[0]) == [1, 2, 6]


def test_rotate_selected(ten_pages, tmp_path):
    out = pages.rotate(ten_pages, tmp_path / "r.pdf", 90, "1, 3")
    with pikepdf.open(out) as pdf:
        assert [int(p.obj.get("/Rotate", 0)) for p in pdf.pages][:4] == [90, 0, 90, 0]


def test_delete_pages(ten_pages, tmp_path):
    out = pages.delete_pages(ten_pages, tmp_path / "d.pdf", "1, 5-end")
    assert page_widths(out) == [1, 2, 3]
    with pytest.raises(RangeError, match="every page"):
        pages.delete_pages(ten_pages, tmp_path / "x.pdf", "1-end")


# ---------- compression ----------
@needs_gs
def test_compress_shrinks_scans(scanned_pdf, tmp_path):
    res = compress_pdf(scanned_pdf, tmp_path / "c.pdf", CompressOptions(dpi=100))
    assert not res.kept_original
    assert res.new_size < res.original_size * 0.5
    with pikepdf.open(res.output) as pdf:
        assert len(pdf.pages) == 3
        assert "/Producer" not in pdf.docinfo  # metadata stripped


def test_compress_keeps_original_when_not_smaller(ten_pages, tmp_path, monkeypatch):
    def fake_gs(args):  # pretend Ghostscript produced a bigger file
        out = next(a for a in args if a.startswith("-sOutputFile=")).split("=", 1)[1]
        pdf = pikepdf.new()
        for _ in range(60):
            pdf.add_blank_page()
        pdf.save(out, object_stream_mode=pikepdf.ObjectStreamMode.disable)
    monkeypatch.setattr("app.core.compress.run_ghostscript", fake_gs)
    res = compress_pdf(ten_pages, tmp_path / "c.pdf", CompressOptions())
    assert res.kept_original and res.output is None
    assert not (tmp_path / "c.pdf").exists()
