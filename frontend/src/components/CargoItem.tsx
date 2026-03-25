import { useState } from "react"
import { ChevronDown, Calendar, TableProperties, LineChart as ChartIcon } from "lucide-react"
import type { Cargo, Contracheque } from "@/types"
import { formatBRL, formatMonthYear } from "@/lib/utils"
import { ContrachequeTable } from "./ContrachequeTable"
import { ContrachequeChart } from "./ContrachequeChart"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"

interface Props {
  cargo: Cargo
  contracheques: Contracheque[]
}

export function CargoItem({ cargo, contracheques }: Props) {
  const [open, setOpen] = useState(false)

  const lastCc = contracheques.length > 0 ? contracheques[contracheques.length - 1] : null

  return (
    <div className="border border-border rounded-lg overflow-hidden bg-card">
      <button
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-muted/40 transition-colors text-left"
      >
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-medium text-sm text-foreground">
              {cargo.cargo || "Sem cargo"}
            </span>
            <Badge variant="outline" className="text-[10px]">
              Mat. {cargo.matricula}
            </Badge>
          </div>
          <div className="flex items-center gap-2 mt-1.5 flex-wrap">
            {cargo.vinculo && (
              <Badge variant="secondary" className="text-[10px]">{cargo.vinculo}</Badge>
            )}
            {cargo.carga_horaria_semanal && (
              <Badge variant="secondary" className="text-[10px]">{cargo.carga_horaria_semanal}h/sem</Badge>
            )}
            {lastCc && (
              <>
                <Badge variant="success" className="text-[10px] font-semibold">
                  Liquido: {formatBRL(lastCc.liquido)}
                </Badge>
                <span className="flex items-center gap-1 text-[10px] text-muted-foreground">
                  <Calendar className="h-3 w-3" aria-hidden="true" />
                  {formatMonthYear(lastCc.referencia_mes, lastCc.referencia_ano)}
                </span>
              </>
            )}
          </div>
        </div>
        <ChevronDown
          aria-hidden="true"
          className={`h-4 w-4 text-muted-foreground shrink-0 transition-transform duration-200 ${
            open ? "rotate-180" : ""
          }`}
        />
      </button>

      {open && (
        <div className="border-t border-border px-4 py-3">
          {contracheques.length === 0 ? (
            <div className="py-8 text-center text-sm text-muted-foreground">
              Nenhum contracheque encontrado.
            </div>
          ) : (
            <Tabs defaultValue="table">
              <TabsList>
                <TabsTrigger value="table">
                  <TableProperties className="h-3.5 w-3.5" aria-hidden="true" />
                  Tabela
                </TabsTrigger>
                <TabsTrigger value="chart">
                  <ChartIcon className="h-3.5 w-3.5" aria-hidden="true" />
                  Grafico
                </TabsTrigger>
              </TabsList>
              <TabsContent value="table">
                <ContrachequeTable contracheques={contracheques} />
              </TabsContent>
              <TabsContent value="chart">
                <ContrachequeChart contracheques={contracheques} />
              </TabsContent>
            </Tabs>
          )}
        </div>
      )}
    </div>
  )
}
