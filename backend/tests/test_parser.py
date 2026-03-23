from datetime import date
from decimal import Decimal

from app.scraping.parser import (
    parse_available_months,
    parse_available_years,
    parse_currency,
    parse_date_br,
    parse_page,
)

SAMPLE_HTML = """
<html><body>
<ul class="nav nav-tabs list">
    <li id="2024"><a href="/230400401/foff/listar-por/funcionarios/202401">2024</a></li>
    <li id="2025"><a href="/230400401/foff/listar-por/funcionarios/202501">2025</a></li>
    <li id="2026" class="active"><a href="/230400401/foff/listar-por/funcionarios/202601">2026</a></li>
</ul>
<ul class="nav nav-pills list">
    <li id="1"><a href="/230400401/foff/listar-por/funcionarios/202601">Janeiro</a></li>
    <li id="2" class="active"><a href="/230400401/foff/listar-por/funcionarios/202602">Fevereiro</a></li>
    <li id="3" class="disabled"><a href="javascript:void(0);">Março</a></li>
    <li id="13"><a href="/230400401/foff/listar-por/funcionarios/202613">13º</a></li>
</ul>
<table id="thetable" class="table table-bordered display">
<thead><tr>
    <th class="details-control"></th>
    <th>Matrícula</th><th>Nome</th><th>Órgão</th><th>Setor</th>
    <th>Cargo</th><th>Cargo2</th><th>Provento</th><th>Desconto</th><th>Líquido</th>
</tr></thead>
<tbody>
    <tr>
        <td class="details-control">
            <div class="hide">
                <div class="row"><h4>Dados pessoais</h4></div>
                <div class="row">
                    <div class="col-lg-2"><strong>CPF</strong><br>223.XXX.XXX-87</div>
                    <div class="col-lg-2"><strong>Data de admissão</strong><br>01/01/1982</div>
                    <div class="col-lg-2"><strong>Vínculo</strong><br>11-EFETIVO COM PORTARIA</div>
                    <div class="col-lg-3"><strong>Carga horária semanal</strong><br>40</div>
                </div>
            </div>
        </td>
        <td class="text-right">0000494</td>
        <td>ABDIAS GOMES NETO</td>
        <td>09-SECRETARIA MUNICIPAL DE EDUCACAO</td>
        <td>0903225-ENS FUNDAMENTAL</td>
        <td>5-AGENTE ADMINISTRATIVO</td>
        <td>572-SUPERVISOR ESCOLAR</td>
        <td class="text-right">R$ 2.431,50</td>
        <td class="text-right">R$ 786,51</td>
        <td class="text-right">R$ 1.644,99</td>
    </tr>
    <tr>
        <td class="details-control">
            <div class="hide">
                <div class="row"><h4>Dados pessoais</h4></div>
                <div class="row">
                    <div class="col-lg-2"><strong>CPF</strong><br>760.XXX.XXX-04</div>
                    <div class="col-lg-2"><strong>Data de admissão</strong><br>02/01/2025</div>
                    <div class="col-lg-2"><strong>Vínculo</strong><br>2-COMISSIONADO</div>
                    <div class="col-lg-3"><strong>Carga horária semanal</strong><br>40</div>
                </div>
            </div>
        </td>
        <td class="text-right">0014234</td>
        <td>ABELARDO FERREIRA GRIGORIO</td>
        <td>09-SECRETARIA MUNICIPAL DE EDUCACAO</td>
        <td>0903134-GESTAO DA SECRETARIA</td>
        <td>551-ORIENTADOR</td>
        <td>551-ORIENTADOR</td>
        <td class="text-right">R$ 1.921,00</td>
        <td class="text-right">R$ 148,57</td>
        <td class="text-right">R$ 1.772,43</td>
    </tr>
</tbody>
</table>
</body></html>
"""


def test_parse_currency():
    assert parse_currency("R$ 2.431,50") == Decimal("2431.50")
    assert parse_currency("R$ 786,51") == Decimal("786.51")
    assert parse_currency("R$ 0,00") == Decimal("0.00")


def test_parse_date_br():
    assert parse_date_br("01/01/1982") == date(1982, 1, 1)
    assert parse_date_br("02/01/2025") == date(2025, 1, 2)
    assert parse_date_br("") is None
    assert parse_date_br("invalid") is None


def test_parse_page():
    records = parse_page(SAMPLE_HTML)
    assert len(records) == 2

    r1 = records[0]
    assert r1.matricula == "0000494"
    assert r1.nome == "ABDIAS GOMES NETO"
    assert r1.orgao == "09-SECRETARIA MUNICIPAL DE EDUCACAO"
    assert r1.cargo == "5-AGENTE ADMINISTRATIVO"
    assert r1.cargo2 == "572-SUPERVISOR ESCOLAR"
    assert r1.provento == Decimal("2431.50")
    assert r1.desconto == Decimal("786.51")
    assert r1.liquido == Decimal("1644.99")
    assert r1.cpf_parcial == "223.XXX.XXX-87"
    assert r1.data_admissao == date(1982, 1, 1)
    assert r1.vinculo == "11-EFETIVO COM PORTARIA"
    assert r1.carga_horaria_semanal == 40

    r2 = records[1]
    assert r2.matricula == "0014234"
    assert r2.nome == "ABELARDO FERREIRA GRIGORIO"
    assert r2.provento == Decimal("1921.00")


def test_parse_available_years():
    years = parse_available_years(SAMPLE_HTML)
    assert years == [2024, 2025, 2026]


def test_parse_available_months():
    months = parse_available_months(SAMPLE_HTML, 2026)
    assert 1 in months
    assert 2 in months
    assert 13 in months
    assert 3 not in months  # disabled


def test_parse_page_empty():
    html = "<html><body><table id='thetable'><tbody></tbody></table></body></html>"
    assert parse_page(html) == []


def test_parse_page_no_table():
    html = "<html><body></body></html>"
    assert parse_page(html) == []
