"""Fork-only: parsing of the Uwagi page into fixed remark fields."""

from librus_mcp.remarks_tools import parse_remarks, to_remark

PAGE = """
<html><body>
<table class="decorated stretch">
  <thead>
    <tr><td colspan="5">Okres 1</td></tr>
    <tr><td>Uwaga</td><td>Data</td><td>Kto dodał</td><td>Rodzaj uwagi</td><td>Kategoria</td></tr>
  </thead>
  <tbody>
    <tr><td>Pomoc  koledze
      na lekcji</td><td>2026-10-01</td><td>Teacher A</td><td>Pozytywna</td><td>Inna</td></tr>
    <tr><td colspan="5">Brak uwag</td></tr>
  </tbody>
</table>
<table class="decorated">
  <thead><tr><td>Uwaga</td><td>Data</td><td>Extra</td></tr></thead>
  <tbody><tr><td>Spóźnienie</td><td>2026-10-02</td><td>x</td></tr></tbody>
</table>
</body></html>
""".encode()


def test_rows_map_to_fixed_fields_and_keep_unknown_columns():
    remarks = [to_remark(row) for row in parse_remarks(PAGE)]
    assert len(remarks) == 2
    first, second = remarks
    assert first.content == "Pomoc koledze na lekcji"
    assert (first.date, first.teacher, first.remark_type, first.category) == (
        "2026-10-01",
        "Teacher A",
        "Pozytywna",
        "Inna",
    )
    assert first.other == []
    assert (second.content, second.date, second.teacher) == ("Spóźnienie", "2026-10-02", "")
    assert [(field.name, field.value) for field in second.other] == [("Extra", "x")]


def test_page_without_tables_has_no_remarks():
    assert parse_remarks(b"<html><body><p>Brak uwag</p></body></html>") == []
