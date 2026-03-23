from decimal import Decimal

from app.scraping.parser import EmployeeRecord
from app.scraping.service import _aggregate_records


def _make_record(matricula="0001", provento="1000", desconto="100", liquido="900", **kw):
    return EmployeeRecord(
        matricula=matricula,
        nome=kw.get("nome", "FULANO"),
        orgao=None, setor=None, cargo=None, cargo2=None,
        provento=Decimal(provento),
        desconto=Decimal(desconto),
        liquido=Decimal(liquido),
        cpf_parcial=None, data_admissao=None, vinculo=None,
        carga_horaria_semanal=None,
    )


def test_aggregate_same_matricula():
    records = [
        _make_record(matricula="0001", provento="1320.00", desconto="368.32", liquido="951.68"),
        _make_record(matricula="0001", provento="424.24", desconto="38.18", liquido="386.06"),
    ]
    result = _aggregate_records(records)
    assert len(result) == 1
    assert result[0].provento == Decimal("1744.24")
    assert result[0].desconto == Decimal("406.50")
    assert result[0].liquido == Decimal("1337.74")


def test_aggregate_different_matriculas():
    records = [
        _make_record(matricula="0001", provento="1000"),
        _make_record(matricula="0002", provento="2000"),
    ]
    result = _aggregate_records(records)
    assert len(result) == 2


def test_aggregate_mixed():
    records = [
        _make_record(matricula="0001", provento="500", desconto="50", liquido="450"),
        _make_record(matricula="0002", provento="800", desconto="80", liquido="720"),
        _make_record(matricula="0001", provento="200", desconto="20", liquido="180"),
    ]
    result = _aggregate_records(records)
    assert len(result) == 2

    by_mat = {r.matricula: r for r in result}
    assert by_mat["0001"].provento == Decimal("700")
    assert by_mat["0001"].desconto == Decimal("70")
    assert by_mat["0001"].liquido == Decimal("630")
    assert by_mat["0002"].provento == Decimal("800")


def test_aggregate_empty():
    assert _aggregate_records([]) == []
