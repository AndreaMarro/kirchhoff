/* Stringhe di presentazione: mai semantica, solo dicitura.
   Ogni chiave sconosciuta passa invariata: meglio il nome grezzo
   del kernel che un'etichetta inventata. */

const KINDS: Record<string, string> = {
  choose_reference: "Riferimento",
  define_nodal_unknowns: "Incognite nodali",
  write_kcl: "KCL al nodo",
  write_voltage_constraint: "Vincolo di tensione",
  serie: "Serie",
  parallelo: "Parallelo",
};

export function kindLabel(kind: string): string {
  return KINDS[kind] ?? kind;
}

const QUANTITIES: Record<string, string> = {
  voltage: "tensione",
  current: "corrente",
};

export function quantityLabel(quantity: string): string {
  return QUANTITIES[quantity] ?? quantity;
}
