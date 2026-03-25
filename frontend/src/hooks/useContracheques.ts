import { useCallback, useEffect, useRef, useState } from "react"
import type { Contracheque } from "@/types"
import { listContracheques } from "@/services/contracheques"

export function useContracheques(cargoId: number, enabled: boolean) {
  const [contracheques, setContracheques] = useState<Contracheque[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const fetched = useRef(false)

  const doFetch = useCallback(async (id: number) => {
    setLoading(true)
    setError(null)
    try {
      const data = await listContracheques(id)
      setContracheques(data)
    } catch {
      setError("Erro ao carregar contracheques.")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (!enabled || fetched.current) return
    fetched.current = true
    doFetch(cargoId)
  }, [cargoId, enabled, doFetch])

  return { contracheques, loading, error }
}
