import { useEffect, useRef, useState } from "react"
import type { FuncionarioDetail } from "@/types"
import { getFuncionario } from "@/services/funcionarios"

export function useFuncionarioDetail(id: number, enabled: boolean) {
  const [detail, setDetail] = useState<FuncionarioDetail | null>(null)
  const [loading, setLoading] = useState(false)
  const fetched = useRef(false)

  useEffect(() => {
    if (!enabled || fetched.current) return
    fetched.current = true
    setLoading(true)
    getFuncionario(id)
      .then(setDetail)
      .catch((err) => console.error("Erro ao buscar detalhe:", err))
      .finally(() => setLoading(false))
  }, [id, enabled])

  return { detail, loading }
}
