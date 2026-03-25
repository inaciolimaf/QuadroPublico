import { ChevronLeft, ChevronRight } from "lucide-react"
import { Button } from "@/components/ui/button"

interface PaginationProps {
  page: number
  totalPages: number
  onPageChange: (page: number) => void
}

export function Pagination({ page, totalPages, onPageChange }: PaginationProps) {
  if (totalPages <= 1) return null

  const pages: number[] = []
  const start = Math.max(0, page - 2)
  const end = Math.min(totalPages - 1, page + 2)
  for (let i = start; i <= end; i++) pages.push(i)

  return (
    <nav className="flex items-center justify-center gap-1" aria-label="Paginacao">
      <Button
        variant="ghost"
        size="icon"
        onClick={() => onPageChange(page - 1)}
        disabled={page === 0}
        aria-label="Pagina anterior"
      >
        <ChevronLeft className="h-4 w-4" aria-hidden="true" />
      </Button>

      {start > 0 && (
        <>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onPageChange(0)}
            aria-label="Ir para pagina 1"
          >
            1
          </Button>
          {start > 1 && <span className="px-1 text-muted-foreground text-sm" aria-hidden="true">...</span>}
        </>
      )}

      {pages.map((p) => (
        <Button
          key={p}
          variant={p === page ? "default" : "ghost"}
          size="sm"
          onClick={() => onPageChange(p)}
          aria-label={`Ir para pagina ${p + 1}`}
          aria-current={p === page ? "page" : undefined}
        >
          {p + 1}
        </Button>
      ))}

      {end < totalPages - 1 && (
        <>
          {end < totalPages - 2 && <span className="px-1 text-muted-foreground text-sm" aria-hidden="true">...</span>}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onPageChange(totalPages - 1)}
            aria-label={`Ir para pagina ${totalPages}`}
          >
            {totalPages}
          </Button>
        </>
      )}

      <Button
        variant="ghost"
        size="icon"
        onClick={() => onPageChange(page + 1)}
        disabled={page >= totalPages - 1}
        aria-label="Proxima pagina"
      >
        <ChevronRight className="h-4 w-4" aria-hidden="true" />
      </Button>
    </nav>
  )
}
