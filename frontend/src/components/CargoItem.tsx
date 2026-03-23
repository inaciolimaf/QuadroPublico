import { useState } from "react"
import { ChevronDown, TableProperties, LineChart as ChartIcon, Calendar } from "lucide-react"
import type { Cargo, Contracheque } from "@/types"
import { formatBRL, formatMonthYear } from "@/lib/utils"
import { ContrachequeTable } from "./ContrachequeTable"
import { ContrachequeChart } from "./ContrachequeChart"

interface Props {
  cargo: Cargo
  contracheques: Contracheque[]
}

export function CargoItem({ cargo, contracheques }: Props) {
  const [open, setOpen] = useState(false)
  const [view, setView] = useState<"table" | "chart">("table")

  const lastCc = contracheques.length > 0 ? contracheques[contracheques.length - 1] : null

  return (
    <div className="border border-zinc-200 rounded-lg overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-zinc-50 transition-colors text-left"
      >
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-medium text-sm">{cargo.cargo || "Sem cargo"}</span>
            <span className="text-xs text-zinc-400">Mat. {cargo.matricula}</span>
          </div>
          <div className="flex items-center gap-3 mt-1 text-xs text-zinc-500 flex-wrap">
            {cargo.vinculo && <span>{cargo.vinculo}</span>}
            {cargo.carga_horaria_semanal && <span>{cargo.carga_horaria_semanal}h/sem</span>}
            {lastCc && (
              <>
                <span className="text-green-700 font-medium">
                  Líquido: {formatBRL(lastCc.liquido)}
                </span>
                <span className="flex items-center gap-1 text-zinc-400">
                  <Calendar className="h-3 w-3" />
                  {formatMonthYear(lastCc.referencia_mes, lastCc.referencia_ano)}
                </span>
              </>
            )}
          </div>
        </div>
        <ChevronDown
          className={`h-4 w-4 text-zinc-400 shrink-0 transition-transform ${
            open ? "rotate-180" : ""
          }`}
        />
      </button>

      {open && (
        <div className="border-t border-zinc-200 px-4 py-3">
          {contracheques.length === 0 ? (
            <div className="py-6 text-center text-sm text-zinc-400">
              Nenhum contracheque encontrado.
            </div>
          ) : (
            <>
              <div className="flex gap-1 mb-3">
                <button
                  onClick={() => setView("table")}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                    view === "table"
                      ? "bg-zinc-900 text-white"
                      : "bg-zinc-100 text-zinc-600 hover:bg-zinc-200"
                  }`}
                >
                  <TableProperties className="h-3.5 w-3.5" />
                  Tabela
                </button>
                <button
                  onClick={() => setView("chart")}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                    view === "chart"
                      ? "bg-zinc-900 text-white"
                      : "bg-zinc-100 text-zinc-600 hover:bg-zinc-200"
                  }`}
                >
                  <ChartIcon className="h-3.5 w-3.5" />
                  Gráfico
                </button>
              </div>

              {view === "table" ? (
                <ContrachequeTable contracheques={contracheques} />
              ) : (
                <ContrachequeChart contracheques={contracheques} />
              )}
            </>
          )}
        </div>
      )}
    </div>
  )
}
