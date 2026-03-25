import { describe, it, expect } from "vitest"
import { render, screen } from "@testing-library/react"
import { Header } from "./Header"

describe("Header", () => {
  it("renderiza titulo QuadroPublico", () => {
    render(<Header />)
    expect(screen.getByText("QuadroPublico")).toBeInTheDocument()
  })

  it("renderiza descricao do portal", () => {
    render(<Header />)
    expect(screen.getByText(/Portal de Transparencia/)).toBeInTheDocument()
  })
})
