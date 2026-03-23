import { Header } from "@/components/Header"
import { FuncionarioList } from "@/components/FuncionarioList"

export default function App() {
  return (
    <div className="min-h-screen bg-zinc-50">
      <Header />
      <main className="mx-auto max-w-5xl px-4 py-6 sm:py-8">
        <FuncionarioList />
      </main>
    </div>
  )
}
