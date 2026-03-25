import { describe, it, expect, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { Pagination } from "./Pagination"

describe("Pagination", () => {
  it("não renderiza quando totalPages <= 1", () => {
    const { container } = render(
      <Pagination page={0} totalPages={1} onPageChange={() => {}} />
    )
    expect(container.innerHTML).toBe("")
  })

  it("renderiza navegação com aria-label", () => {
    render(<Pagination page={0} totalPages={5} onPageChange={() => {}} />)
    expect(screen.getByRole("navigation", { name: "Paginação" })).toBeInTheDocument()
  })

  it("desabilita botão anterior na primeira página", () => {
    render(<Pagination page={0} totalPages={5} onPageChange={() => {}} />)
    expect(screen.getByRole("button", { name: "Página anterior" })).toBeDisabled()
  })

  it("desabilita botão próxima na última página", () => {
    render(<Pagination page={4} totalPages={5} onPageChange={() => {}} />)
    expect(screen.getByRole("button", { name: "Próxima página" })).toBeDisabled()
  })

  it("chama onPageChange ao clicar próxima", async () => {
    const onPageChange = vi.fn()
    render(<Pagination page={0} totalPages={5} onPageChange={onPageChange} />)
    await userEvent.click(screen.getByRole("button", { name: "Próxima página" }))
    expect(onPageChange).toHaveBeenCalledWith(1)
  })

  it("marca página atual com aria-current", () => {
    render(<Pagination page={2} totalPages={5} onPageChange={() => {}} />)
    expect(screen.getByRole("button", { name: "Ir para página 3" })).toHaveAttribute("aria-current", "page")
  })
})
