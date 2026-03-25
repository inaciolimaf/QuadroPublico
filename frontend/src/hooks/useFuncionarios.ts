import { useCallback, useEffect, useState } from "react"
import type { Funcionario } from "@/types"
import { listFuncionarios } from "@/services/funcionarios"
import { useDebounce } from "./useDebounce"

const PAGE_SIZE = 20

export function useFuncionarios() {
  const [query, setQuery] = useState("")
  const [page, setPage] = useState(0)
  const [funcionarios, setFuncionarios] = useState<Funcionario[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const debouncedQuery = useDebounce(query, 400)

  const fetchData = useCallback(async (q: string, p: number) => {
    setLoading(true)
    setError(null)
    try {
      const data = await listFuncionarios({
        q: q || undefined,
        skip: p * PAGE_SIZE,
        limit: PAGE_SIZE,
      })
      setFuncionarios(data.items)
      setTotal(data.total)
    } catch {
      setError("Erro ao buscar funcionários. Tente novamente.")
      setFuncionarios([])
      setTotal(0)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    setPage(0)
  }, [debouncedQuery])

  useEffect(() => {
    fetchData(debouncedQuery, page)
  }, [debouncedQuery, page, fetchData])

  return {
    funcionarios,
    total,
    loading,
    error,
    query,
    setQuery,
    page,
    setPage,
    pageSize: PAGE_SIZE,
    totalPages: Math.ceil(total / PAGE_SIZE),
  }
}
