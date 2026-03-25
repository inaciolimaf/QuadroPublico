import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts"
import type { Contracheque } from "@/types"
import { formatBRL, formatMonthYear } from "@/lib/utils"

interface Props {
  contracheques: Contracheque[]
}

export function ContrachequeChart({ contracheques }: Props) {
  const data = contracheques.map((cc) => ({
    label: formatMonthYear(cc.referencia_mes, cc.referencia_ano),
    provento: parseFloat(cc.provento),
    desconto: parseFloat(cc.desconto),
    liquido: parseFloat(cc.liquido),
  }))

  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="oklch(0.88 0.008 247)" />
          <XAxis
            dataKey="label"
            tick={{ fontSize: 11, fill: "oklch(0.55 0.015 247)" }}
            interval="preserveStartEnd"
          />
          <YAxis
            tick={{ fontSize: 11, fill: "oklch(0.55 0.015 247)" }}
            tickFormatter={(v: number) =>
              new Intl.NumberFormat("pt-BR", {
                notation: "compact",
                compactDisplay: "short",
              }).format(v)
            }
          />
          <Tooltip
            formatter={(value) => formatBRL(Number(value))}
            labelStyle={{ fontWeight: 600 }}
            contentStyle={{
              borderRadius: "0.5rem",
              border: "1px solid oklch(0.88 0.008 247)",
              boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
            }}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="provento"
            name="Provento"
            stroke="oklch(0.52 0.14 150)"
            strokeWidth={2}
            dot={false}
          />
          <Line
            type="monotone"
            dataKey="desconto"
            name="Desconto"
            stroke="oklch(0.55 0.2 27)"
            strokeWidth={2}
            dot={false}
          />
          <Line
            type="monotone"
            dataKey="liquido"
            name="Liquido"
            stroke="oklch(0.35 0.07 255)"
            strokeWidth={2}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
