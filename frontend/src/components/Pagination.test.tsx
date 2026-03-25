import { describe, it, expect, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { Pagination } from "./Pagination"

describe("Pagination", () => {
  it("nao renderiza quando totalPages <= 1", () => {
    const { container } = render(
      <Pagination page={0} totalPages={1} onPageChange={() => {}} />
    )
    expect(container.innerHTML).toBe("")
  })

  it("renderiza navegacao com aria-label", () => {
    render(<Pagination page={0} totalPages={5} onPageChange={() => {}} />)
    expect(screen.getByRole("navigation", { name: "Paginacao" })).toBeInTheDocument()
  })

  it("desabilita botao anterior na primeira pagina", () => {
    render(<Pagination page={0} totalPages={5} onPageChange={() => {}} />)
    expect(screen.getByRole("button", { name: "Pagina anterior" })).toBeDisabled()
  })

  it("desabilita botao proxima na ultima pagina", () => {
    render(<Pagination page={4} totalPages={5} onPageChange={() => {}} />)
    expect(screen.getByRole("button", { name: "Proxima pagina" })).toBeDisabled()
  })

  it("chama onPageChange ao clicar proxima", async () => {
    const onPageChange = vi.fn()
    render(<Pagination page={0} totalPages={5} onPageChange={onPageChange} />)
    await userEvent.click(screen.getByRole("button", { name: "Proxima pagina" }))
    expect(onPageChange).toHaveBeenCalledWith(1)
  })

  it("marca pagina atual com aria-current", () => {
    render(<Pagination page={2} totalPages={5} onPageChange={() => {}} />)
    expect(screen.getByRole("button", { name: "Ir para pagina 3" })).toHaveAttribute("aria-current", "page")
  })
})
