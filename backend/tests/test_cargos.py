from datetime import date

from app.models import Cargo, Funcionario


def _seed(db):
    f = Funcionario(nome="FUNC TEST", cpf_parcial="111.XXX.XXX-22")
    db.add(f)
    db.flush()
    c = Cargo(
        funcionario_id=f.id,
        matricula="0000494",
        cargo="5-AGENTE ADMINISTRATIVO",
        orgao="09-SECRETARIA MUNICIPAL DE EDUCACAO",
        data_admissao=date(1982, 1, 1),
        vinculo="11-EFETIVO COM PORTARIA",
        carga_horaria_semanal=40,
    )
    db.add(c)
    db.commit()
    db.refresh(f)
    db.refresh(c)
    return f, c


def test_list_cargos(client, db):
    f, c = _seed(db)
    resp = client.get(f"/funcionarios/{f.id}/cargos/")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["matricula"] == "0000494"


def test_get_cargo_detail(client, db):
    f, c = _seed(db)
    resp = client.get(f"/funcionarios/{f.id}/cargos/{c.id}")
    assert resp.status_code == 200
    assert "contracheques" in resp.json()
    assert resp.json()["cargo"] == "5-AGENTE ADMINISTRATIVO"


def test_cargo_funcionario_not_found(client):
    resp = client.get("/funcionarios/9999/cargos/")
    assert resp.status_code == 404


def test_cargo_not_found(client, db):
    f, _ = _seed(db)
    resp = client.get(f"/funcionarios/{f.id}/cargos/9999")
    assert resp.status_code == 404
