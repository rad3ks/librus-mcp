"""Behaviour remarks (uwagi) from Synergia's Uwagi page.

Fork-only addition: `librus-python-api` 1.9.0 has no public remarks read, only
the internal `behaviour_notes_probe` endpoint (GET /uwagi, no side effect). This
module reads that page through the account's authenticated session and parses
its tables. Field names come from the observed Polish column headers; any other
column is kept in `other` so nothing is dropped silently.
"""

from typing import Any, cast

from lxml import html  # type: ignore[import-untyped]
from mcp.server.mcpserver import Context, MCPServer
from mcp.types import ToolAnnotations

from librus_mcp.read_schemas import AccountAliasInput
from librus_mcp.runtime import Runtime
from librus_mcp.schemas import WireModel

REMARKS_ENDPOINT = "behaviour_notes_probe"
MAX_REMARKS = 500
MAX_CELL_LENGTH = 4000

HEADER_FIELDS = {
    "uwaga": "content",
    "treść": "content",
    "data": "date",
    "kto dodał": "teacher",
    "nauczyciel": "teacher",
    "rodzaj uwagi": "remark_type",
    "typ": "remark_type",
    "kategoria": "category",
}


class RemarkExtraField(WireModel):
    name: str
    value: str


class Remark(WireModel):
    content: str
    date: str
    teacher: str
    remark_type: str
    category: str
    other: list[RemarkExtraField]


class RemarksResult(WireModel):
    items: list[Remark]
    count: int


def _cell_text(element: Any) -> str:
    return " ".join(element.text_content().split())[:MAX_CELL_LENGTH]


def parse_remarks(body: bytes) -> list[dict[str, str]]:
    """Rows of every `decorated` table, keyed by the table's last header row."""
    # Synergia serves UTF-8; do not let lxml guess latin-1 when no charset is declared.
    document = html.fromstring(body, parser=html.HTMLParser(encoding="utf-8"))
    rows: list[dict[str, str]] = []
    tables = document.xpath(
        "//table[contains(concat(' ', normalize-space(@class), ' '), ' decorated ')]"
    )
    for table in tables:
        headers = [
            _cell_text(cell)
            for cell in table.xpath("./thead//tr[last()]/td | ./thead//tr[last()]/th")
        ]
        for row in table.xpath("./tbody/tr"):
            cells = row.xpath("./td")
            if len(cells) < 2:
                continue  # "Brak uwag" placeholder or separator row
            values = [_cell_text(cell) for cell in cells]
            keys = headers if len(headers) == len(values) else [""] * len(values)
            rows.append(
                {
                    (key or f"column_{index}"): value
                    for index, (key, value) in enumerate(zip(keys, values))
                }
            )
            if len(rows) >= MAX_REMARKS:
                return rows
    return rows


def to_remark(row: dict[str, str]) -> Remark:
    known = dict.fromkeys(("content", "date", "teacher", "remark_type", "category"), "")
    seen: set[str] = set()
    other: list[RemarkExtraField] = []
    for header, value in row.items():
        target = HEADER_FIELDS.get(header.strip().lower())
        if target and target not in seen:
            known[target] = value
            seen.add(target)
        else:
            other.append(RemarkExtraField(name=header, value=value))
    return Remark(**known, other=other)


def register_remarks_tools(server: MCPServer[Runtime]) -> None:
    ordinary = ToolAnnotations(read_only_hint=True, open_world_hint=True)
    server.tool(title="Remarks", annotations=ordinary)(get_remarks)


async def get_remarks(
    account_alias: AccountAliasInput,
    ctx: Context[Runtime, Any],
) -> RemarksResult:
    """List the student's behaviour remarks (uwagi): positive and negative notes from teachers with content, date, teacher, remark type and category, as the Uwagi page shows them. Does not mark anything read in Librus."""
    runtime = ctx.request_context.lifespan_context
    client = runtime.account(account_alias)

    async def fetch(budget: Any, _: bool) -> list[dict[str, str]]:
        return await client._page(REMARKS_ENDPOINT, budget, parse_remarks)

    # The library types _read keys as its own operation names; this one is the
    # probe endpoint's name, used only as a cache/admission key.
    rows = await client._read(
        cast(Any, (REMARKS_ENDPOINT,)), fetch, runtime.budget, 0.0, endpoint=REMARKS_ENDPOINT
    )
    items = [to_remark(row) for row in rows]
    return RemarksResult(items=items, count=len(items))
