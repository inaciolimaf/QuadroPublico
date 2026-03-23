from datetime import date

from app.models import Cargo, Contracheque, Funcionario


def test_funcionario_repr():
    f = Funcionario(nome="ABDIAS GOMES NETO", cpf_parcial="223.XXX.XXX-87")
    assert "ABDIAS GOMES NETO" in repr(f)
    assert "223.XXX.XXX-87" in repr(f)


def test_cargo_repr():
    c = Cargo(matricula="0000494", cargo="5-AGENTE ADMINISTRATIVO")
    assert "0000494" in repr(c)
    assert "5-AGENTE ADMINISTRATIVO" in repr(c)


def test_contracheque_repr():
    c = Contracheque(cargo_id=1, referencia_mes=3, referencia_ano=2026)
    assert "3/2026" in repr(c)


def test_funcionario_has_cargos():
    f = Funcionario(nome="MARIA SILVA", cpf_parcial="111.XXX.XXX-22")
    assert f.nome == "MARIA SILVA"


def test_cargo_fields():
    c = Cargo(
        matricula="0000494",
        orgao="09-SECRETARIA MUNICIPAL DE EDUCACAO",
        setor="0903225-ENS FUNDAMENTAL (1 AO 5) EFETIVOS",
        cargo="5-AGENTE ADMINISTRATIVO",
        cargo2="572-SUPERVISOR ESCOLAR",
        data_admissao=date(1982, 1, 1),
        vinculo="11-EFETIVO COM PORTARIA",
        carga_horaria_semanal=40,
    )
    assert c.data_admissao == date(1982, 1, 1)
    assert c.carga_horaria_semanal == 40
    assert c.vinculo == "11-EFETIVO COM PORTARIA"


def test_contracheque_fields():
    c = Contracheque(
        cargo_id=1,
        provento=2431.50,
        desconto=786.51,
        liquido=1644.99,
        referencia_mes=3,
        referencia_ano=2026,
    )
    assert c.provento == 2431.50
    assert c.desconto == 786.51
    assert c.liquido == 1644.99
