import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass
class EmployeeRecord:
    matricula: str
    nome: str
    orgao: str | None
    setor: str | None
    cargo: str | None
    cargo2: str | None
    provento: Decimal
    desconto: Decimal
    liquido: Decimal
    cpf_parcial: str | None
    data_admissao: date | None
    vinculo: str | None
    carga_horaria_semanal: int | None


def parse_currency(value: str) -> Decimal:
    cleaned = value.replace("R$", "").replace(".", "").replace(",", ".").strip()
    return Decimal(cleaned) if cleaned else Decimal("0")


def parse_date_br(value: str) -> date | None:
    value = value.strip()
    if not value:
        return None
    try:
        parts = value.split("/")
        return date(int(parts[2]), int(parts[1]), int(parts[0]))
    except (IndexError, ValueError):
        return None


def parse_int_safe(value: str) -> int | None:
    value = value.strip()
    try:
        return int(value)
    except ValueError:
        return None


_TAG_RE = re.compile(r"<[^>]+>")
_TD_RE = re.compile(r"<td[^>]*>(.*?)</td>", re.DOTALL)
_TR_RE = re.compile(r"<tr[^>]*>(.*?)</tr>", re.DOTALL)

_CPF_RE = re.compile(
    r"<strong>[^<]*CPF[^<]*</strong>\s*(?:<br\s*/?>)?\s*([^<]+)", re.IGNORECASE
)
_DATA_ADM_RE = re.compile(
    r"<strong>[^<]*Data de admiss[^<]*</strong>\s*(?:<br\s*/?>)?\s*([^<]+)", re.IGNORECASE
)
_VINCULO_RE = re.compile(
    r"<strong>[^<]*nculo[^<]*</strong>\s*(?:<br\s*/?>)?\s*([^<]+)", re.IGNORECASE
)
_CARGA_RE = re.compile(
    r"<strong>[^<]*Carga hor[^<]*</strong>\s*(?:<br\s*/?>)?\s*([^<]+)", re.IGNORECASE
)


def _strip_tags(s: str) -> str:
    return _TAG_RE.sub("", s).strip()


def _extract_detail(html: str, pattern: re.Pattern) -> str:
    m = pattern.search(html)
    return m.group(1).strip() if m else ""


def _find_table(html: str) -> str | None:
    table_start = html.find('id="thetable"')
    if table_start == -1:
        return None
    table_start = html.rfind("<table", 0, table_start)
    table_end = html.find("</table>", table_start)
    if table_end == -1:
        return None
    return html[table_start:table_end]


def _parse_row(tr_content: str) -> EmployeeRecord | None:
    if "details-control" not in tr_content:
        return None

    tds = _TD_RE.findall(tr_content)
    if len(tds) < 8:
        return None

    detail_html = tds[0]
    return EmployeeRecord(
        matricula=_strip_tags(tds[1]),
        nome=_strip_tags(tds[2]),
        orgao=_strip_tags(tds[3]) or None,
        setor=_strip_tags(tds[4]) or None,
        cargo=_strip_tags(tds[5]) or None,
        cargo2=_strip_tags(tds[6]) or None,
        provento=parse_currency(_strip_tags(tds[-3])),
        desconto=parse_currency(_strip_tags(tds[-2])),
        liquido=parse_currency(_strip_tags(tds[-1])),
        cpf_parcial=_extract_detail(detail_html, _CPF_RE) or None,
        data_admissao=parse_date_br(_extract_detail(detail_html, _DATA_ADM_RE)),
        vinculo=_extract_detail(detail_html, _VINCULO_RE) or None,
        carga_horaria_semanal=parse_int_safe(_extract_detail(detail_html, _CARGA_RE)),
    )


def parse_page(html: str) -> list[EmployeeRecord]:
    table_html = _find_table(html)
    if not table_html:
        return []

    records: list[EmployeeRecord] = []
    for tr_match in _TR_RE.finditer(table_html):
        record = _parse_row(tr_match.group(1))
        if record:
            records.append(record)
    return records


def parse_available_months(html: str, year: int) -> list[int]:
    months: list[int] = []
    for li_match in re.finditer(r"(<li[^>]*>)(.*?)</li>", html, re.DOTALL):
        li_tag = li_match.group(1)
        if "disabled" in li_tag:
            continue
        li_body = li_match.group(2)
        href_match = re.search(rf'href="[^"]*/{year}(\d{{2}})"', li_body)
        if href_match:
            month = int(href_match.group(1))
            if month not in months:
                months.append(month)
    return months


def parse_available_years(html: str) -> list[int]:
    years: set[int] = set()
    for m in re.finditer(r'class="nav-tabs".*?</ul>', html, re.DOTALL):
        for href in re.finditer(r'href="[^"]*?/(\d{4})\d{2}"', m.group()):
            years.add(int(href.group(1)))
    if not years:
        for m in re.finditer(r'nav-tabs.*?</ul>', html, re.DOTALL):
            for href in re.finditer(r'href="[^"]*?/(\d{4})\d{2}"', m.group()):
                years.add(int(href.group(1)))
    return sorted(years)
