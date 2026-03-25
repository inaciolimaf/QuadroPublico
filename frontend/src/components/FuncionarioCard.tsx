import { useCallback, useEffect, useRef, useState } from "react"
import { ChevronDown, User, Building2, Briefcase, AlertCircle } from "lucide-react"
import type { Contracheque, Funcionario } from "@/types"
import { useFuncionarioDetail } from "@/hooks/useFuncionarioDetail"
import { listContracheques } from "@/services/contracheques"
import { CargoItem } from "./CargoItem"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Separator } from "@/components/ui/separator"

interface Props {
  funcionario: Funcionario
}

export function FuncionarioCard({ funcionario }: Props) {
  const [open, setOpen] = useState(false)
  const { detail, loading, error } = useFuncionarioDetail(funcionario.id, open)
  const [contrachequesByCargo, setContrachequesByCargo] = useState<Record<number, Contracheque[]>>({})
  const [loadingCc, setLoadingCc] = useState(false)
  const [errorCc, setErrorCc] = useState<string | null>(null)
  const fetchedCc = useRef(false)

  const fetchContracheques = useCallback(async (cargos: { id: number }[]) => {
    setLoadingCc(true)
    setErrorCc(null)
    try {
      const results = await Promise.all(
        cargos.map((cargo) =>
          listContracheques(cargo.id).then((ccs) => [cargo.id, ccs] as const)
        )
      )
      const map: Record<number, Contracheque[]> = {}
      for (const [cargoId, ccs] of results) {
        map[cargoId] = ccs
      }
      setContrachequesByCargo(map)
    } catch {
      setErrorCc("Erro ao carregar contracheques.")
    } finally {
      setLoadingCc(false)
    }
  }, [])

  useEffect(() => {
    if (!detail?.cargos?.length || fetchedCc.current) return
    fetchedCc.current = true
    fetchContracheques(detail.cargos)
  }, [detail, fetchContracheques])

  const latestCargo = detail?.cargos?.[0] ?? null
  const displayError = error || errorCc

  return (
    <Card className="overflow-hidden transition-shadow hover:shadow-md">
      <button
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        className="w-full text-left px-5 py-4 hover:bg-muted/30 transition-colors"
      >
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 shrink-0">
                <User className="h-4 w-4 text-primary" aria-hidden="true" />
              </div>
              <h3 className="font-semibold text-foreground truncate">
                {funcionario.nome}
              </h3>
            </div>

            {latestCargo && (
              <div className="mt-2.5 ml-10.5 flex flex-wrap items-center gap-2">
                {latestCargo.orgao && (
                  <Badge variant="secondary" className="gap-1">
                    <Building2 className="h-3 w-3" aria-hidden="true" />
                    {latestCargo.orgao}
                  </Badge>
                )}
                {latestCargo.cargo && (
                  <Badge variant="outline" className="gap-1">
                    <Briefcase className="h-3 w-3" aria-hidden="true" />
                    {latestCargo.cargo}
                  </Badge>
                )}
              </div>
            )}
          </div>

          <ChevronDown
            aria-hidden="true"
            className={`h-5 w-5 text-muted-foreground shrink-0 mt-1.5 transition-transform duration-200 ${
              open ? "rotate-180" : ""
            }`}
          />
        </div>
      </button>

      {open && (
        <>
          <Separator />
          <div className="px-5 py-4" role="region" aria-label={`Detalhes de ${funcionario.nome}`}>
            {displayError ? (
              <div className="flex items-center gap-2 text-sm text-destructive py-4" role="alert">
                <AlertCircle className="h-4 w-4 shrink-0" aria-hidden="true" />
                {displayError}
              </div>
            ) : loading || loadingCc ? (
              <div className="space-y-3" aria-busy="true" aria-label="Carregando...">
                <Skeleton className="h-5 w-32" />
                <Skeleton className="h-16" />
                <Skeleton className="h-16" />
              </div>
            ) : detail && detail.cargos.length > 0 ? (
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    Vinculos
                  </h4>
                  <Badge variant="secondary" className="text-[10px] px-1.5 py-0">
                    {detail.cargos.length}
                  </Badge>
                </div>
                {detail.cargos.map((cargo) => (
                  <CargoItem
                    key={cargo.id}
                    cargo={cargo}
                    contracheques={contrachequesByCargo[cargo.id] ?? []}
                  />
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground text-center py-6">
                Nenhum cargo encontrado.
              </p>
            )}
          </div>
        </>
      )}
    </Card>
  )
}
