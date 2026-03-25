import { Landmark } from "lucide-react"

export function Header() {
  return (
    <header className="bg-primary text-primary-foreground border-b-4 border-primary/80">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-4 py-6 sm:py-8">
          <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-white/10">
            <Landmark className="h-6 w-6" aria-hidden="true" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">
              QuadroPublico
            </h1>
            <p className="mt-1 text-sm text-primary-foreground/70 max-w-xl">
              Portal de Transparencia dos Servidores Municipais
            </p>
          </div>
        </div>
      </div>
    </header>
  )
}
