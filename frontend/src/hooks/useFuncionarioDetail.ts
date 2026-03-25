import { useCallback, useEffect, useRef, useState } from "react"
import type { FuncionarioDetail } from "@/types"
import { getFuncionario } from "@/services/funcionarios"

export function useFuncionarioDetail(id: number, enabled: boolean) {
  const [detail, setDetail] = useState<FuncionarioDetail | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const fetched = useRef(false)

  const doFetch = useCallback(async (funcId: number) => {
    setLoading(true)
    setError(null)
    try {
      const data = await getFuncionario(funcId)
      setDetail(data)
    } catch {
      setError("Erro ao carregar detalhes do funcionário.")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (!enabled || fetched.current) return
    fetched.current = true
    doFetch(id)
  }, [id, enabled, doFetch])

  return { detail, loading, error }
}
