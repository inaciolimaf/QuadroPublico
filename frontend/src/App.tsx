import { Header } from "@/components/Header"
import { FuncionarioList } from "@/components/FuncionarioList"
import { Footer } from "@/components/Footer"

export default function App() {
  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Header />
      <main className="flex-1 mx-auto w-full max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
        <FuncionarioList />
      </main>
      <Footer />
    </div>
  )
}
