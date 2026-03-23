from app.models import Funcionario


def _seed(db):
    names = [
        "MARIA ZENILDA TABOSA",
        "ANTONIA ZENILDA SILVA",
        "ZENILDA LIMA",
        "ANTONIA MARIA ZENILDA",
        "JOSE CARLOS SILVA",
    ]
    funcs = []
    for name in names:
        f = Funcionario(nome=name)
        db.add(f)
        funcs.append(f)
    db.commit()
    for f in funcs:
        db.refresh(f)
    return funcs


def test_list_funcionarios(client, db):
    _seed(db)
    resp = client.get("/funcionarios/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 5
    assert len(data["items"]) == 5


def test_list_funcionarios_empty(client):
    resp = client.get("/funcionarios/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["items"] == []


def test_search_both_terms_required(client, db):
    _seed(db)
    resp = client.get("/funcionarios/", params={"q": "maria zenilda"})
    data = resp.json()
    names = [f["nome"] for f in data["items"]]
    assert "MARIA ZENILDA TABOSA" in names
    assert "ANTONIA MARIA ZENILDA" in names
    assert "ANTONIA ZENILDA SILVA" not in names
    assert "ZENILDA LIMA" not in names
    assert data["total"] == 2


def test_search_case_insensitive(client, db):
    _seed(db)
    resp = client.get("/funcionarios/", params={"q": "MariA ZenildA"})
    assert resp.json()["total"] >= 2


def test_search_single_term(client, db):
    _seed(db)
    resp = client.get("/funcionarios/", params={"q": "zenilda"})
    data = resp.json()
    names = [f["nome"] for f in data["items"]]
    assert "JOSE CARLOS SILVA" not in names
    assert data["total"] == 4


def test_search_no_results(client, db):
    _seed(db)
    resp = client.get("/funcionarios/", params={"q": "joao pedro"})
    assert resp.json()["items"] == []
    assert resp.json()["total"] == 0


def test_search_unordered(client, db):
    _seed(db)
    resp = client.get("/funcionarios/", params={"q": "zenilda maria"})
    names = [f["nome"] for f in resp.json()["items"]]
    assert "MARIA ZENILDA TABOSA" in names
    assert "ANTONIA MARIA ZENILDA" in names


def test_pagination(client, db):
    _seed(db)
    resp = client.get("/funcionarios/", params={"skip": 0, "limit": 2})
    data = resp.json()
    assert len(data["items"]) == 2
    assert data["total"] == 5


def test_get_funcionario(client, db):
    funcs = _seed(db)
    resp = client.get(f"/funcionarios/{funcs[0].id}")
    assert resp.status_code == 200
    assert resp.json()["nome"] == "MARIA ZENILDA TABOSA"
    assert "cargos" in resp.json()


def test_get_funcionario_not_found(client):
    resp = client.get("/funcionarios/9999")
    assert resp.status_code == 404
