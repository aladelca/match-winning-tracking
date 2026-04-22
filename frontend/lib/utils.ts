import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function resolveFixtureDate(
  kickoffIso: string | null,
  eventDate: string | null = null,
): Date | null {
  if (kickoffIso) {
    return new Date(kickoffIso);
  }

  if (eventDate) {
    return new Date(`${eventDate}T12:00:00.000Z`);
  }

  return null;
}

export function formatKickoff(
  kickoffIso: string | null,
  eventDate: string | null = null,
): string {
  const date = resolveFixtureDate(kickoffIso, eventDate);
  if (!date) {
    return "Fecha por confirmar";
  }

  return new Intl.DateTimeFormat("es-PE", {
    dateStyle: "medium",
    ...(kickoffIso ? { timeStyle: "short" as const } : {}),
    timeZone: "America/Lima",
  }).format(date);
}

export function formatPercent(value: number, digits: number = 1): string {
  return `${(value * 100).toFixed(digits)}%`;
}
