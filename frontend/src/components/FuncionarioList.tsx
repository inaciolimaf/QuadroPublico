import { useFuncionarios } from "@/hooks/useFuncionarios"
import { SearchBar } from "./SearchBar"
import { FuncionarioCard } from "./FuncionarioCard"
import { Pagination } from "./Pagination"
import { Skeleton } from "@/components/ui/skeleton"
import { Card, CardContent } from "@/components/ui/card"
import { Users, AlertCircle, Search } from "lucide-react"

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
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-foreground mb-1">Consulta de Servidores</h2>
        <p className="text-sm text-muted-foreground mb-4">
          Pesquise por nome para consultar remuneracoes, cargos e historico de contracheques.
        </p>
        <SearchBar value={query} onChange={setQuery} />
        <div className="mt-2 h-5 text-xs text-muted-foreground" aria-live="polite">
          {total > 0 && (
            <span className="flex items-center gap-1">
              <Users className="h-3 w-3" aria-hidden="true" />
              {total.toLocaleString("pt-BR")} servidor{total !== 1 ? "es" : ""} encontrado{total !== 1 ? "s" : ""}
            </span>
          )}
          {loading && "Buscando..."}
        </div>
      </div>

      <div className="space-y-3">
        {error ? (
          <Card>
            <CardContent className="flex flex-col items-center py-12">
              <AlertCircle className="h-10 w-10 text-destructive mb-3" aria-hidden="true" />
              <p className="text-sm text-destructive font-medium" role="alert">{error}</p>
            </CardContent>
          </Card>
        ) : loading ? (
          <div aria-busy="true" aria-label="Carregando servidores" className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-[72px] rounded-xl" />
            ))}
          </div>
        ) : funcionarios.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center py-16 text-muted-foreground">
              <Search className="h-12 w-12 mb-4 opacity-30" aria-hidden="true" />
              <p className="text-sm font-medium">Nenhum servidor encontrado</p>
              {query && (
                <p className="text-xs mt-1">Tente buscar por outro nome.</p>
              )}
            </CardContent>
          </Card>
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
