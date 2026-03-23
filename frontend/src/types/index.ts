export interface Funcionario {
  id: number
  nome: string
  cpf_parcial: string | null
  criado_em: string
  atualizado_em: string
}

export interface Cargo {
  id: number
  funcionario_id: number
  matricula: string
  orgao: string | null
  setor: string | null
  cargo: string | null
  cargo2: string | null
  data_admissao: string | null
  vinculo: string | null
  carga_horaria_semanal: number | null
  criado_em: string
  atualizado_em: string
}

export interface FuncionarioDetail extends Funcionario {
  cargos: Cargo[]
}

export interface Contracheque {
  id: number
  cargo_id: number
  provento: string
  desconto: string
  liquido: string
  referencia_mes: number
  referencia_ano: number
  criado_em: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
}
