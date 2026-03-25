import { describe, it, expect } from "vitest"
import { formatBRL, formatMonthYear } from "./utils"

describe("formatBRL", () => {
  it("formata número como moeda brasileira", () => {
    expect(formatBRL(1234.56)).toBe("R$\u00a01.234,56")
  })

  it("formata string numérica", () => {
    expect(formatBRL("5000")).toBe("R$\u00a05.000,00")
  })

  it("retorna R$ 0,00 para zero", () => {
    expect(formatBRL(0)).toBe("R$\u00a00,00")
  })
})

describe("formatMonthYear", () => {
  it("formata mês/ano corretamente", () => {
    expect(formatMonthYear(1, 2024)).toBe("Jan/2024")
    expect(formatMonthYear(6, 2023)).toBe("Jun/2023")
    expect(formatMonthYear(12, 2025)).toBe("Dez/2025")
  })

  it("formata 13º salário", () => {
    expect(formatMonthYear(13, 2024)).toBe("13º/2024")
  })

  it("fallback para mês fora do range", () => {
    expect(formatMonthYear(14, 2024)).toBe("14/2024")
  })
})
