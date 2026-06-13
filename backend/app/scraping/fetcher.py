import re

import requests

BASE_URL = "https://folha.governotransparente.com.br/230400401/foff/listar-por/funcionarios"
TIMEOUT = 60
MAX_PAGES = 1000

_DATA_PAGE_RE = re.compile(r'data-page="(\d+)"')


def _ref_url(year: int, month: int) -> str:
    ref = f"{year}{month:02d}"
    return f"{BASE_URL}/{ref}"


def fetch_page(year: int, month: int) -> str:
    """Busca apenas a primeira página (GET). Usado na descoberta de períodos."""
    resp = requests.get(_ref_url(year, month), timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.text


def _fetch_paginated(url: str, page: int) -> str:
    resp = requests.post(
        url,
        data={"page": page, "nome": "", "tipo_vinculo": "", "tipo_orgao": ""},
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    return resp.text


def _max_page(html: str) -> int:
    pages = _DATA_PAGE_RE.findall(html)
    return max((int(p) for p in pages), default=1)


def fetch_all_pages(year: int, month: int) -> list[str]:
    """Busca TODAS as páginas do período.

    A fonte pagina no servidor (15 registros por página) via POST com o campo
    ``page``. A primeira página (GET) expõe no paginador o número da última
    página (link ``»``), que é usado para percorrer o restante.
    """
    url = _ref_url(year, month)
    first = fetch_page(year, month)
    total = min(_max_page(first), MAX_PAGES)

    pages = [first]
    for page in range(2, total + 1):
        pages.append(_fetch_paginated(url, page))
    return pages
