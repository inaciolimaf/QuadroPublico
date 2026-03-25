import { ChevronLeft, ChevronRight } from "lucide-react"

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
    <nav className="flex items-center justify-center gap-1 mt-6" aria-label="Paginação">
      <button
        onClick={() => onPageChange(page - 1)}
        disabled={page === 0}
        aria-label="Página anterior"
        className="p-2 rounded-md hover:bg-zinc-100 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
      >
        <ChevronLeft className="h-4 w-4" aria-hidden="true" />
      </button>

      {start > 0 && (
        <>
          <button
            onClick={() => onPageChange(0)}
            aria-label="Ir para página 1"
            className="px-3 py-1 rounded-md text-sm hover:bg-zinc-100 transition-colors"
          >
            1
          </button>
          {start > 1 && <span className="px-1 text-zinc-400" aria-hidden="true">...</span>}
        </>
      )}

      {pages.map((p) => (
        <button
          key={p}
          onClick={() => onPageChange(p)}
          aria-label={`Ir para página ${p + 1}`}
          aria-current={p === page ? "page" : undefined}
          className={`px-3 py-1 rounded-md text-sm transition-colors ${
            p === page
              ? "bg-zinc-900 text-white"
              : "hover:bg-zinc-100"
          }`}
        >
          {p + 1}
        </button>
      ))}

      {end < totalPages - 1 && (
        <>
          {end < totalPages - 2 && <span className="px-1 text-zinc-400" aria-hidden="true">...</span>}
          <button
            onClick={() => onPageChange(totalPages - 1)}
            aria-label={`Ir para página ${totalPages}`}
            className="px-3 py-1 rounded-md text-sm hover:bg-zinc-100 transition-colors"
          >
            {totalPages}
          </button>
        </>
      )}

      <button
        onClick={() => onPageChange(page + 1)}
        disabled={page >= totalPages - 1}
        aria-label="Próxima página"
        className="p-2 rounded-md hover:bg-zinc-100 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
      >
        <ChevronRight className="h-4 w-4" aria-hidden="true" />
      </button>
    </nav>
  )
}
