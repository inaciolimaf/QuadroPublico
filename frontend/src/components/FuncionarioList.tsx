import { useFuncionarios } from "@/hooks/useFuncionarios"
import { SearchBar } from "./SearchBar"
import { FuncionarioCard } from "./FuncionarioCard"
import { Pagination } from "./Pagination"
import { Users, AlertCircle } from "lucide-react"

export function FuncionarioList() {
  const {
    funcionarios,
    total,
    loading,
    error,
    query,
    setQuery,
    page,
    setPage,
    totalPages,
  } = useFuncionarios()

  return (
    <div>
      <SearchBar value={query} onChange={setQuery} />

      <div className="mt-3 flex items-center justify-between text-xs text-zinc-400">
        <span aria-live="polite">
          {total > 0 ? (
            <>
              <Users className="inline h-3 w-3 mr-1" aria-hidden="true" />
              {total} funcionário{total !== 1 ? "s" : ""} encontrado{total !== 1 ? "s" : ""}
            </>
          ) : loading ? (
            "Buscando..."
          ) : (
            ""
          )}
        </span>
      </div>

      <div className="mt-4 space-y-3">
        {error ? (
          <div className="text-center py-12" role="alert">
            <AlertCircle className="h-10 w-10 mx-auto mb-3 text-red-400" aria-hidden="true" />
            <p className="text-sm text-red-600">{error}</p>
          </div>
        ) : loading ? (
          <div aria-busy="true" aria-label="Carregando funcionários" className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-16 rounded-xl bg-zinc-100 animate-pulse" />
            ))}
          </div>
        ) : funcionarios.length === 0 ? (
          <div className="text-center py-12 text-zinc-400">
            <Users className="h-10 w-10 mx-auto mb-3 opacity-40" aria-hidden="true" />
            <p className="text-sm">Nenhum funcionário encontrado.</p>
            {query && (
              <p className="text-xs mt-1">
                Tente buscar por outro nome.
              </p>
            )}
          </div>
        ) : (
          funcionarios.map((f) => (
            <FuncionarioCard key={f.id} funcionario={f} />
          ))
        )}
      </div>

      <Pagination page={page} totalPages={totalPages} onPageChange={setPage} />
    </div>
  )
}
