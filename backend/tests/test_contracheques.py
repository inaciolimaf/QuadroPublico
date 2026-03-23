from decimal import Decimal

from app.models import Cargo, Contracheque, Funcionario


def _seed(db):
    f = Funcionario(nome="FUNC CONTRACHEQUE TEST")
    db.add(f)
    db.flush()
    c = Cargo(funcionario_id=f.id, matricula="0001")
    db.add(c)
    db.flush()
    cc = Contracheque(
        cargo_id=c.id,
        provento=Decimal("2431.50"),
        desconto=Decimal("786.51"),
        liquido=Decimal("1644.99"),
        referencia_mes=3,
        referencia_ano=2026,
    )
    db.add(cc)
    db.commit()
    db.refresh(c)
    db.refresh(cc)
    return c, cc


def test_list_contracheques(client, db):
    c, cc = _seed(db)
    resp = client.get(f"/cargos/{c.id}/contracheques/")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["provento"] == "2431.50"


def test_get_contracheque(client, db):
    c, cc = _seed(db)
    resp = client.get(f"/cargos/{c.id}/contracheques/{cc.id}")
    assert resp.status_code == 200
    assert resp.json()["referencia_mes"] == 3
    assert resp.json()["liquido"] == "1644.99"


def test_contracheque_cargo_not_found(client):
    resp = client.get("/cargos/9999/contracheques/")
    assert resp.status_code == 404


def test_contracheque_not_found(client, db):
    c, _ = _seed(db)
    resp = client.get(f"/cargos/{c.id}/contracheques/9999")
    assert resp.status_code == 404
