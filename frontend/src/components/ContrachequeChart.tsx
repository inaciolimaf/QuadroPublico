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
          <CartesianGrid strokeDasharray="3 3" stroke="#e4e4e7" />
          <XAxis
            dataKey="label"
            tick={{ fontSize: 11 }}
            interval="preserveStartEnd"
          />
          <YAxis
            tick={{ fontSize: 11 }}
            tickFormatter={(v: number) =>
              new Intl.NumberFormat("pt-BR", {
                notation: "compact",
                compactDisplay: "short",
              }).format(v)
            }
          />
          <Tooltip
            formatter={(value: number) => formatBRL(value)}
            labelStyle={{ fontWeight: 600 }}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="provento"
            name="Provento"
            stroke="#16a34a"
            strokeWidth={2}
            dot={false}
          />
          <Line
            type="monotone"
            dataKey="desconto"
            name="Desconto"
            stroke="#dc2626"
            strokeWidth={2}
            dot={false}
          />
          <Line
            type="monotone"
            dataKey="liquido"
            name="Líquido"
            stroke="#2563eb"
            strokeWidth={2}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
