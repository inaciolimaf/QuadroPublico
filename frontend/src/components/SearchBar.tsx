import { Search, X } from "lucide-react"

interface SearchBarProps {
  value: string
  onChange: (value: string) => void
}

export function SearchBar({ value, onChange }: SearchBarProps) {
  return (
    <div className="relative">
      <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-400" aria-hidden="true" />
      <label htmlFor="search-funcionario" className="sr-only">Buscar funcionário por nome</label>
      <input
        id="search-funcionario"
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Buscar funcionário por nome..."
        maxLength={200}
        className="w-full rounded-lg border border-zinc-300 bg-white py-2.5 pl-10 pr-10 text-sm
          placeholder:text-zinc-400 focus:border-zinc-500 focus:outline-none focus:ring-1
          focus:ring-zinc-500 transition-colors"
      />
      {value && (
        <button
          onClick={() => onChange("")}
          aria-label="Limpar busca"
          className="absolute right-3 top-1/2 -translate-y-1/2 p-0.5 rounded-full
            text-zinc-400 hover:text-zinc-600 hover:bg-zinc-100 transition-colors"
        >
          <X className="h-4 w-4" aria-hidden="true" />
        </button>
      )}
    </div>
  )
}
