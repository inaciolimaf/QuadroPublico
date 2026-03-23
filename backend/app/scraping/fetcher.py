import requests

BASE_URL = "https://folha.governotransparente.com.br/230400401/foff/listar-por/funcionarios"

TIMEOUT = 60


def fetch_page(year: int, month: int) -> str:
    """Busca o HTML de uma página de folha para ano/mês."""
    ref = f"{year}{month:02d}"
    url = f"{BASE_URL}/{ref}"
    print(f"[FETCH] Buscando {url}")
    resp = requests.get(url, timeout=TIMEOUT)
    resp.raise_for_status()
    print(f"[FETCH] {url} -> {resp.status_code} ({len(resp.text)} bytes)")
    return resp.text
