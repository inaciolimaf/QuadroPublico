import type { Contracheque } from "@/types"
import { formatBRL, formatMonthYear } from "@/lib/utils"
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table"

interface Props {
  contracheques: Contracheque[]
}

export function ContrachequeTable({ contracheques }: Props) {
  return (
    <Table>
      <TableHeader>
        <TableRow className="hover:bg-transparent">
          <TableHead>Referencia</TableHead>
          <TableHead className="text-right">Provento</TableHead>
          <TableHead className="text-right">Desconto</TableHead>
          <TableHead className="text-right">Liquido</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {[...contracheques].reverse().map((cc) => (
          <TableRow key={cc.id}>
            <TableCell className="font-medium">
              {formatMonthYear(cc.referencia_mes, cc.referencia_ano)}
            </TableCell>
            <TableCell className="text-right text-success">
              {formatBRL(cc.provento)}
            </TableCell>
            <TableCell className="text-right text-destructive">
              {formatBRL(cc.desconto)}
            </TableCell>
            <TableCell className="text-right font-semibold">
              {formatBRL(cc.liquido)}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
