import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from bs4 import BeautifulSoup, Tag


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
    """'01/01/1982' -> date(1982, 1, 1)"""
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


def _extract_detail(div: Tag, label: str) -> str:
    """Extrai valor de um campo do bloco 'Dados pessoais'."""
    strong = div.find("strong", string=re.compile(label, re.IGNORECASE))
    if not strong:
        return ""
    # O texto vem depois do <br> como text node solto
    parent = strong.parent
    if parent is None:
        return ""
    texts = list(parent.stripped_strings)
    # texts = ['CPF', '223.XXX.XXX-87'] ou ['Carga horária semanal', '40']
    return texts[1] if len(texts) > 1 else ""


def parse_page(html: str) -> list[EmployeeRecord]:
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", id="thetable")
    if not table:
        return []

    records: list[EmployeeRecord] = []

    for tr in table.find_all("tr"):
        tds = tr.find_all("td")
        if not tds:
            continue

        # Primeira <td> tem class details-control e contém o bloco de dados pessoais
        detail_td = tds[0]
        if "details-control" not in detail_td.get("class", []):
            continue

        # Extrair dados pessoais do div escondido
        hidden_div = detail_td.find("div", class_="hide")
        cpf = _extract_detail(hidden_div, "CPF") if hidden_div else ""
        data_adm_str = _extract_detail(hidden_div, "Data de admiss") if hidden_div else ""
        vinculo = _extract_detail(hidden_div, "nculo") if hidden_div else ""
        carga_str = _extract_detail(hidden_div, "Carga hor") if hidden_div else ""

        # Extrair colunas da tabela
        # tds[0]=details, tds[1]=matricula, tds[2]=nome, tds[3]=orgao,
        # tds[4]=setor, tds[5]=cargo, tds[6]=cargo2,
        # tds[-3]=provento, tds[-2]=desconto, tds[-1]=liquido
        if len(tds) < 8:
            continue

        matricula = tds[1].get_text(strip=True)
        nome = tds[2].get_text(strip=True)
        orgao = tds[3].get_text(strip=True) or None
        setor = tds[4].get_text(strip=True) or None
        cargo = tds[5].get_text(strip=True) or None
        cargo2 = tds[6].get_text(strip=True) or None
        provento = parse_currency(tds[-3].get_text(strip=True))
        desconto = parse_currency(tds[-2].get_text(strip=True))
        liquido = parse_currency(tds[-1].get_text(strip=True))

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
    soup = BeautifulSoup(html, "html.parser")
    pills = soup.select(".nav-pills li")
    months: list[int] = []
    for li in pills:
        if "disabled" in li.get("class", []):
            continue
        a = li.find("a")
        if not a or not a.get("href"):
            continue
        href = a["href"]
        match = re.search(rf"{year}(\d{{2}})$", href)
        if match:
            months.append(int(match.group(1)))
    return months


def parse_available_years(html: str) -> list[int]:
    """Retorna lista de anos disponíveis nas tabs."""
    soup = BeautifulSoup(html, "html.parser")
    tabs = soup.select(".nav-tabs li")
    years: list[int] = []
    for li in tabs:
        a = li.find("a")
        if not a or not a.get("href"):
            continue
        match = re.search(r"/(\d{4})\d{2}$", a["href"])
        if match:
            years.append(int(match.group(1)))
    return sorted(set(years))
