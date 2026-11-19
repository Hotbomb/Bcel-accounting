// Laos uses UTC+7 all year (no daylight saving), so a fixed offset is exact.
export const VIENTIANE_OFFSET_MINUTES = 7 * 60;
const OFFSET_MS = VIENTIANE_OFFSET_MINUTES * 60_000;

/** Parts of a moment as seen on a clock in Vientiane. */
export function vientianeParts(d: Date) {
  const local = new Date(d.getTime() + OFFSET_MS);
  return {
    year: local.getUTCFullYear(),
    month: local.getUTCMonth() + 1,
    day: local.getUTCDate(),
    hour: local.getUTCHours(),
    minute: local.getUTCMinutes(),
    weekday: local.getUTCDay(), // 0 = Sunday
  };
}

/** The real moment for a Vientiane wall-clock time. */
export function fromVientiane(year: number, month: number, day: number, hour = 0, minute = 0, second = 0): Date {
  return new Date(Date.UTC(year, month - 1, day, hour, minute, second) - OFFSET_MS);
}

export function monthKey(d: Date = new Date()): string {
  const p = vientianeParts(d);
  return `${p.year}-${String(p.month).padStart(2, "0")}`;
}

export function startOfDay(d: Date): Date {
  const p = vientianeParts(d);
  return fromVientiane(p.year, p.month, p.day);
}

/** Weeks start on Monday. */
export function startOfWeek(d: Date): Date {
  const p = vientianeParts(d);
  const daysSinceMonday = (p.weekday + 6) % 7;
  return fromVientiane(p.year, p.month, p.day - daysSinceMonday);
}

export function startOfMonth(d: Date): Date {
  const p = vientianeParts(d);
  return fromVientiane(p.year, p.month, 1);
}

export function addMonths(d: Date, n: number): Date {
  const p = vientianeParts(d);
  return fromVientiane(p.year, p.month + n, 1);
}

/** "2026-11-18" for a date in Vientiane. */
export function dayKey(d: Date): string {
  const p = vientianeParts(d);
  return `${p.year}-${String(p.month).padStart(2, "0")}-${String(p.day).padStart(2, "0")}`;
}

/** Value for <input type="datetime-local"> in Vientiane time. */
export function toLocalInputValue(d: Date): string {
  const p = vientianeParts(d);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${p.year}-${pad(p.month)}-${pad(p.day)}T${pad(p.hour)}:${pad(p.minute)}`;
}

/** Parse "2026-11-18T20:40" or "2026-11-18T20:40:19" as Vientiane time. */
export function parseLocalDateTime(s: string): Date | null {
  const m = /^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})(?::(\d{2}))?$/.exec(s.trim());
  if (!m) return null;
  const [, y, mo, d, h, mi, se] = m.map((x) => (x === undefined ? undefined : Number(x))) as number[];
  if (mo < 1 || mo > 12 || d < 1 || d > 31 || h > 23 || mi > 59 || (se ?? 0) > 59) return null;
  const date = fromVientiane(y, mo, d, h, mi, se ?? 0);
  const back = vientianeParts(date);
  if (back.day !== d || back.month !== mo) return null; // e.g. 31 February
  return date;
}
