import type { Funcionario, FuncionarioDetail, PaginatedResponse } from "@/types"
import { fetchJson } from "./api"

export function listFuncionarios(params: {
  q?: string
  skip?: number
  limit?: number
}): Promise<PaginatedResponse<Funcionario>> {
  const search = new URLSearchParams()
  if (params.q) search.set("q", params.q)
  if (params.skip !== undefined) search.set("skip", String(params.skip))
  if (params.limit !== undefined) search.set("limit", String(params.limit))
  return fetchJson(`/funcionarios/?${search.toString()}`)
}

export function getFuncionario(id: number): Promise<FuncionarioDetail> {
  return fetchJson(`/funcionarios/${id}`)
}
