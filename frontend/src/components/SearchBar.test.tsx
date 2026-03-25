import { describe, it, expect, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { SearchBar } from "./SearchBar"

describe("SearchBar", () => {
  it("renderiza input com placeholder", () => {
    render(<SearchBar value="" onChange={() => {}} />)
    expect(screen.getByPlaceholderText("Buscar funcionário por nome...")).toBeInTheDocument()
  })

  it("chama onChange ao digitar", async () => {
    const onChange = vi.fn()
    render(<SearchBar value="" onChange={onChange} />)
    const input = screen.getByRole("textbox")
    await userEvent.type(input, "a")
    expect(onChange).toHaveBeenCalledWith("a")
  })

  it("mostra botão limpar quando tem valor", () => {
    render(<SearchBar value="teste" onChange={() => {}} />)
    expect(screen.getByRole("button", { name: "Limpar busca" })).toBeInTheDocument()
  })

  it("não mostra botão limpar quando vazio", () => {
    render(<SearchBar value="" onChange={() => {}} />)
    expect(screen.queryByRole("button", { name: "Limpar busca" })).not.toBeInTheDocument()
  })

  it("chama onChange com string vazia ao clicar limpar", async () => {
    const onChange = vi.fn()
    render(<SearchBar value="teste" onChange={onChange} />)
    await userEvent.click(screen.getByRole("button", { name: "Limpar busca" }))
    expect(onChange).toHaveBeenCalledWith("")
  })

  it("tem maxLength de 200 caracteres", () => {
    render(<SearchBar value="" onChange={() => {}} />)
    expect(screen.getByRole("textbox")).toHaveAttribute("maxLength", "200")
  })

  it("tem label acessível", () => {
    render(<SearchBar value="" onChange={() => {}} />)
    expect(screen.getByLabelText("Buscar funcionário por nome")).toBeInTheDocument()
  })
})
