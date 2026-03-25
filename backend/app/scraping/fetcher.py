import requests

BASE_URL = "https://folha.governotransparente.com.br/230400401/foff/listar-por/funcionarios"
TIMEOUT = 60


def fetch_page(year: int, month: int) -> str:
    ref = f"{year}{month:02d}"
    url = f"{BASE_URL}/{ref}"
    resp = requests.get(url, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.text
