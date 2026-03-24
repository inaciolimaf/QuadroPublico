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
    """'R$ 2.431,50' -> Decimal('2431.50')"""
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


# ---------- Regex patterns (compilados uma vez) ----------

_TAG_RE = re.compile(r"<[^>]+>")
_TD_RE = re.compile(r"<td[^>]*>(.*?)</td>", re.DOTALL)

# Detalhes do bloco hidden
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

# Row pattern: <tr> que contém details-control
_TR_RE = re.compile(r"<tr[^>]*>(.*?)</tr>", re.DOTALL)


def _strip_tags(s: str) -> str:
    return _TAG_RE.sub("", s).strip()


def _extract_detail(html: str, pattern: re.Pattern) -> str:
    m = pattern.search(html)
    return m.group(1).strip() if m else ""


def parse_page(html: str) -> list[EmployeeRecord]:
    # Localiza a tabela por string search (evita parsear o HTML inteiro)
    table_start = html.find('id="thetable"')
    if table_start == -1:
        return []
    # Vai para o início do <table
    table_start = html.rfind("<table", 0, table_start)
    table_end = html.find("</table>", table_start)
    if table_end == -1:
        return []
    table_html = html[table_start:table_end]

    records: list[EmployeeRecord] = []

    for tr_match in _TR_RE.finditer(table_html):
        tr_content = tr_match.group(1)

        if "details-control" not in tr_content:
            continue

        tds = _TD_RE.findall(tr_content)
        if len(tds) < 8:
            continue

        # Primeiro TD: bloco de detalhes (CPF, data admissão, etc.)
        detail_html = tds[0]
        cpf = _extract_detail(detail_html, _CPF_RE)
        data_adm_str = _extract_detail(detail_html, _DATA_ADM_RE)
        vinculo = _extract_detail(detail_html, _VINCULO_RE)
        carga_str = _extract_detail(detail_html, _CARGA_RE)

        # Demais TDs: texto simples
        matricula = _strip_tags(tds[1])
        nome = _strip_tags(tds[2])
        orgao = _strip_tags(tds[3]) or None
        setor = _strip_tags(tds[4]) or None
        cargo = _strip_tags(tds[5]) or None
        cargo2 = _strip_tags(tds[6]) or None
        provento = parse_currency(_strip_tags(tds[-3]))
        desconto = parse_currency(_strip_tags(tds[-2]))
        liquido = parse_currency(_strip_tags(tds[-1]))

        records.append(
            EmployeeRecord(
                matricula=matricula,
                nome=nome,
                orgao=orgao,
                setor=setor,
                cargo=cargo,
                cargo2=cargo2,
                provento=provento,
                desconto=desconto,
                liquido=liquido,
                cpf_parcial=cpf or None,
                data_admissao=parse_date_br(data_adm_str),
                vinculo=vinculo or None,
                carga_horaria_semanal=parse_int_safe(carga_str),
            )
        )

    return records


def parse_available_months(html: str, year: int) -> list[int]:
    """Retorna lista de meses disponíveis (não disabled) para um dado ano."""
    nav_start = html.find("nav-pills")
    if nav_start == -1:
        return []
    nav_end = html.find("</ul>", nav_start)
    if nav_end == -1:
        return []
    nav_html = html[nav_start:nav_end]

    months: list[int] = []
    for li_match in re.finditer(r"<li[^>]*>(.*?)</li>", nav_html, re.DOTALL):
        li_html = li_match.group(0)
        if "disabled" in li_html:
            continue
        href_match = re.search(rf'href="[^"]*?{year}(\d{{2}})"', li_html)
        if href_match:
            months.append(int(href_match.group(1)))
    return months


def parse_available_years(html: str) -> list[int]:
    """Retorna lista de anos disponíveis nas tabs."""
    nav_start = html.find("nav-tabs")
    if nav_start == -1:
        return []
    nav_end = html.find("</ul>", nav_start)
    if nav_end == -1:
        return []
    nav_html = html[nav_start:nav_end]

    years: set[int] = set()
    for m in re.finditer(r'href="[^"]*?/(\d{4})\d{2}"', nav_html):
        years.add(int(m.group(1)))
    return sorted(years)
