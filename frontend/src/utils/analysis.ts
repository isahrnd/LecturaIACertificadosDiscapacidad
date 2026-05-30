import type { Analysis, DomainKey } from "../types/analysis";

export const DOMAIN_LABELS: Record<DomainKey, string> = {
  cognicion: "Cognición",
  movilidad: "Movilidad",
  cuidado_personal: "Cuidado personal",
  relaciones: "Relaciones",
  vida_diaria: "Vida diaria",
  participacion: "Participación",
};

export function getInitials(name: string): string {
  const trimmed = name.trim();
  if (!trimmed) {
    return "IA";
  }
  const parts = trimmed.split(/\s+/).slice(0, 2);
  return parts.map((part) => part[0]?.toUpperCase() ?? "").join("") || "IA";
}

export function formatLocation(analysis: Analysis): string {
  const { municipio, departamento } = analysis.persona;
  if (municipio && departamento) {
    return `${municipio}, ${departamento}`;
  }
  return municipio || departamento || "Ubicación no disponible";
}

export function formatCertificationDate(value: string): string {
  if (!value) {
    return "Fecha no disponible";
  }
  const trimmed = value.trim();
  const dayFirstMatch = trimmed.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
  let parsed: Date;

  if (dayFirstMatch) {
    const [, day, month, year] = dayFirstMatch;
    parsed = new Date(Number(year), Number(month) - 1, Number(day));
  } else {
    parsed = new Date(trimmed);
  }

  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat("es-CO", {
    day: "numeric",
    month: "short",
    year: "numeric",
  }).format(parsed);
}

export function stripAdjustmentTitlePrefix(value: string): string {
  const trimmed = value.trim();
  if (!trimmed) {
    return trimmed;
  }

  return trimmed.replace(/^\[[^\]]+\]\s*/u, "").trim() || trimmed;
}

export function getAdjustmentsHeading(activeConditions: string[]): string {
  const cleaned = activeConditions.map((item) => item.trim()).filter(Boolean);
  if (cleaned.length !== 1) {
    return "Con ajustes razonables";
  }

  return `Con ajustes razonables para discapacidad ${cleaned[0].toLowerCase()}`;
}

export function toDisplayList(items: string[], fallback: string): string[] {
  const cleaned = items.map((item) => item.trim()).filter(Boolean);
  return cleaned.length > 0 ? cleaned : [fallback];
}

export function getDomainTone(value: number) {
  if (value >= 75) {
    return {
      text: "text-terracotta-700",
      bar: "bg-terracotta-500",
      halo: "bg-gradient-to-br from-terracotta-50 to-white",
    };
  }

  if (value >= 50) {
    return {
      text: "text-blue-700",
      bar: "bg-blue-500",
      halo: "bg-gradient-to-br from-[#eef8f7] to-white",
    };
  }

  return {
    text: "text-almia-700",
    bar: "bg-almia-400",
    halo: "bg-gradient-to-br from-almia-50 to-white",
  };
}

export function clampMetric(value: number): number {
  if (Number.isNaN(value)) {
    return 0;
  }
  return Math.max(0, Math.min(100, value));
}

export function splitIntoColumns(items: string[], columns: number): string[][] {
  const buckets = Array.from({ length: columns }, () => [] as string[]);
  items.forEach((item, index) => {
    buckets[index % columns].push(item);
  });
  return buckets;
}
