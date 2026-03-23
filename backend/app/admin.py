from sqladmin import Admin, ModelView

from app.database import engine
from app.models import Cargo, Contracheque, Funcionario


class FuncionarioAdmin(ModelView, model=Funcionario):
    column_list = [Funcionario.id, Funcionario.nome, Funcionario.cpf_parcial, Funcionario.criado_em]
    column_searchable_list = [Funcionario.nome, Funcionario.cpf_parcial]
    name = "Funcionário"
    name_plural = "Funcionários"


class CargoAdmin(ModelView, model=Cargo):
    column_list = [Cargo.id, Cargo.matricula, Cargo.cargo, Cargo.orgao, Cargo.vinculo, Cargo.funcionario_id]
    column_searchable_list = [Cargo.matricula, Cargo.cargo]
    name = "Cargo"
    name_plural = "Cargos"


class ContrachequeAdmin(ModelView, model=Contracheque):
    column_list = [
        Contracheque.id, Contracheque.cargo_id,
        Contracheque.provento, Contracheque.desconto, Contracheque.liquido,
        Contracheque.referencia_mes, Contracheque.referencia_ano,
    ]
    name = "Contracheque"
    name_plural = "Contracheques"


def setup_admin(app):
    admin = Admin(app, engine, title="QuadroPublico Admin")
    admin.add_view(FuncionarioAdmin)
    admin.add_view(CargoAdmin)
    admin.add_view(ContrachequeAdmin)
