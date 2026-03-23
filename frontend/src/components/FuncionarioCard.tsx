import { useEffect, useRef, useState } from "react"
import { ChevronDown, User, Building2, Briefcase } from "lucide-react"
import type { Cargo, Contracheque, Funcionario } from "@/types"
import { useFuncionarioDetail } from "@/hooks/useFuncionarioDetail"
import { listContracheques } from "@/services/contracheques"
import { CargoItem } from "./CargoItem"

interface Props {
  funcionario: Funcionario
}

export function FuncionarioCard({ funcionario }: Props) {
  const [open, setOpen] = useState(false)
  const { detail, loading } = useFuncionarioDetail(funcionario.id, open)
  const [contrachequesByCargo, setContrachequesByCargo] = useState<Record<number, Contracheque[]>>({})
  const [loadingCc, setLoadingCc] = useState(false)
  const fetchedCc = useRef(false)

  // Quando os cargos carregam, busca contracheques de todos em paralelo
  useEffect(() => {
    if (!detail?.cargos?.length || fetchedCc.current) return
    fetchedCc.current = true
    setLoadingCc(true)

    Promise.all(
      detail.cargos.map((cargo) =>
        listContracheques(cargo.id).then((ccs) => [cargo.id, ccs] as const)
      )
    )
      .then((results) => {
        const map: Record<number, Contracheque[]> = {}
        for (const [cargoId, ccs] of results) {
          map[cargoId] = ccs
        }
        setContrachequesByCargo(map)
      })
      .catch((err) => console.error("Erro ao buscar contracheques:", err))
      .finally(() => setLoadingCc(false))
  }, [detail])

  const latestCargo = detail?.cargos?.[0] ?? null

  // Último contracheque do cargo mais recente (para preview)
  const getLastCc = (cargo: Cargo): Contracheque | null => {
    const ccs = contrachequesByCargo[cargo.id]
    return ccs?.length ? ccs[ccs.length - 1] : null
  }

  const latestCc = latestCargo ? getLastCc(latestCargo) : null

  return (
    <div className="rounded-xl border border-zinc-200 bg-white shadow-sm overflow-hidden transition-shadow hover:shadow-md">
      <button
        onClick={() => setOpen(!open)}
        className="w-full text-left px-4 py-4 sm:px-5 hover:bg-zinc-50/50 transition-colors"
      >
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <User className="h-4 w-4 text-zinc-400 shrink-0" />
              <h3 className="font-semibold text-zinc-900 truncate">
                {funcionario.nome}
              </h3>
            </div>

            {latestCargo && (
              <div className="mt-2 flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-3 text-xs text-zinc-500">
                {latestCargo.orgao && (
                  <span className="flex items-center gap-1">
                    <Building2 className="h-3 w-3" />
                    <span className="truncate">{latestCargo.orgao}</span>
                  </span>
                )}
                {latestCargo.cargo && (
                  <span className="flex items-center gap-1">
                    <Briefcase className="h-3 w-3" />
                    <span className="truncate">{latestCargo.cargo}</span>
                  </span>
                )}
              </div>
            )}
          </div>

          <ChevronDown
            className={`h-5 w-5 text-zinc-400 shrink-0 mt-0.5 transition-transform ${
              open ? "rotate-180" : ""
            }`}
          />
        </div>
      </button>

      {open && (
        <div className="border-t border-zinc-100 px-4 py-4 sm:px-5">
          {loading || loadingCc ? (
            <div className="space-y-3">
              {[1, 2].map((i) => (
                <div key={i} className="h-16 rounded-lg bg-zinc-100 animate-pulse" />
              ))}
            </div>
          ) : detail && detail.cargos.length > 0 ? (
            <div className="space-y-2">
              <h4 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-3">
                Cargos ({detail.cargos.length})
              </h4>
              {detail.cargos.map((cargo) => (
                <CargoItem
                  key={cargo.id}
                  cargo={cargo}
                  contracheques={contrachequesByCargo[cargo.id] ?? []}
                />
              ))}
            </div>
          ) : (
            <p className="text-sm text-zinc-400 text-center py-4">
              Nenhum cargo encontrado.
            </p>
          )}
        </div>
      )}
    </div>
  )
}
