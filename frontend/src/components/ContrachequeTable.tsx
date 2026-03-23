import type { Contracheque } from "@/types"
import { formatBRL, formatMonthYear } from "@/lib/utils"

interface Props {
  contracheques: Contracheque[]
}

export function ContrachequeTable({ contracheques }: Props) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-zinc-200 text-left text-zinc-500">
            <th className="py-2 pr-4 font-medium">Referência</th>
            <th className="py-2 pr-4 font-medium text-right">Provento</th>
            <th className="py-2 pr-4 font-medium text-right">Desconto</th>
            <th className="py-2 font-medium text-right">Líquido</th>
          </tr>
        </thead>
        <tbody>
          {[...contracheques].reverse().map((cc) => (
            <tr key={cc.id} className="border-b border-zinc-100 hover:bg-zinc-50 transition-colors">
              <td className="py-2 pr-4">
                {formatMonthYear(cc.referencia_mes, cc.referencia_ano)}
              </td>
              <td className="py-2 pr-4 text-right text-green-700">
                {formatBRL(cc.provento)}
              </td>
              <td className="py-2 pr-4 text-right text-red-600">
                {formatBRL(cc.desconto)}
              </td>
              <td className="py-2 text-right font-medium">
                {formatBRL(cc.liquido)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
