import type { Contracheque } from "@/types"
import { fetchJson } from "./api"

export function listContracheques(cargoId: number): Promise<Contracheque[]> {
  return fetchJson(`/cargos/${cargoId}/contracheques/`)
}
