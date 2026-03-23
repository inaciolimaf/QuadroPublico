import { useEffect, useRef, useState } from "react"
import type { Contracheque } from "@/types"
import { listContracheques } from "@/services/contracheques"

export function useContracheques(cargoId: number, enabled: boolean) {
  const [contracheques, setContracheques] = useState<Contracheque[]>([])
  const [loading, setLoading] = useState(false)
  const fetched = useRef(false)

  useEffect(() => {
    if (!enabled || fetched.current) return
    fetched.current = true
    setLoading(true)
    listContracheques(cargoId)
      .then(setContracheques)
      .catch((err) => console.error("Erro ao buscar contracheques:", err))
      .finally(() => setLoading(false))
  }, [cargoId, enabled])

  return { contracheques, loading }
}
