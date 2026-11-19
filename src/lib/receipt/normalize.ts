import { parseLocalDateTime, vientianeParts } from "../time";
import type { Extraction } from "./schema";

export const CONFIDENCE_THRESHOLD = 0.8;

export interface OwnAccount {
  account_masked: string;
  holder_name: string | null;
}

export interface NormalizeContext {
  ownAccounts: OwnAccount[];
  /** Kip per 1 THB from the most recent exchange receipt, if any. */
  latestThbRate: number | null;
}

export interface TransactionDraft {
  kind: "expense" | "own_transfer";
  status: "confirmed" | "needs_review";
  review_reasons: string[];
  occurred_at: string; // ISO
  amount: number;
  currency: string;
  amount_lak: number | null;
  fee: number | null;
  to_amount: number | null;
  to_currency: string | null;
  exchange_rate: number | null;
  receipt_type: Extraction["receipt_type"];
  counterparty_name: string | null;
  counterparty_account: string | null;
  from_account: string | null;
  transaction_ref: string | null;
  ticket_ref: string | null;
  dedupe_key: string;
  memo: string | null;
  category: string;
  confidence: number;
}

/**
 * Mask any long run of digits so at most the last 3 digits of a run of 5 or
 * more are kept. BCEL already masks accounts ("222-12-xxxxx254"); this is a
 * safety net in case a full number ever appears.
 */
export function maskAccount(s: string | null | undefined): string | null {
  if (!s) return null;
  const trimmed = s.replace(/\s+/g, "").trim();
  if (!trimmed) return null;
  return trimmed.replace(/\d{5,}/g, (run) => "x".repeat(run.length - 3) + run.slice(-3));
}

/** Compare names ignoring case, spaces and titles like MR / MRS / MS. */
export function normalizeName(s: string | null | undefined): string {
  if (!s) return "";
  return s
    .toUpperCase()
    .replace(/\b(MR|MRS|MS|MISS|DR)\.?\b/g, "")
    .replace(/[^\p{L}\p{N}]/gu, "");
}

export function cleanMemo(s: string | null | undefined): string | null {
  if (!s) return null;
  const t = s.trim();
  if (!t || /^[.\-–—_\s]+$/.test(t)) return null;
  return t.slice(0, 500);
}

export function cleanRef(s: string | null | undefined): string | null {
  if (!s) return null;
  const t = s.replace(/\s+/g, "").trim();
  if (!t || !/^[A-Za-z0-9]{6,40}$/.test(t)) return null;
  return t;
}

function cleanCurrency(s: string | null | undefined): string | null {
  if (!s) return null;
  const t = s.trim().toUpperCase();
  return /^[A-Z]{3}$/.test(t) ? t : null;
}

function cleanAmount(n: number | null | undefined): number | null {
  if (n === null || n === undefined || !Number.isFinite(n) || n < 0) return null;
  return Math.round(n * 100) / 100;
}

/** The fallback duplicate key: amount + minute + recipient. */
export function makeDedupeKey(amount: number, currency: string, occurredAt: Date, counterparty: string | null): string {
  const minute = Math.floor(occurredAt.getTime() / 60_000);
  return `${currency}:${amount}:${minute}:${normalizeName(counterparty)}`;
}

/** Bill numbers start with YYYYMMDD; check they match the printed date. */
function refMatchesDate(ref: string | null, occurredAt: Date): boolean | null {
  if (!ref || !/^\d{8}/.test(ref)) return null;
  const p = vientianeParts(occurredAt);
  const expected = `${p.year}${String(p.month).padStart(2, "0")}${String(p.day).padStart(2, "0")}`;
  return ref.startsWith(expected);
}

export function isOwnAccount(account: string | null, ctx: NormalizeContext): boolean {
  if (!account) return false;
  const a = account.toLowerCase();
  return ctx.ownAccounts.some((o) => o.account_masked.toLowerCase() === a);
}

/**
 * Turn the AI's raw answer into a transaction ready to save, and decide whether
 * it needs a human to check it. Returns null if it is not a usable receipt.
 */
export function normalizeExtraction(x: Extraction, ctx: NormalizeContext): TransactionDraft | null {
  if (!x.is_bcel_receipt) return null;

  const reasons: string[] = [];

  const amount = cleanAmount(x.amount);
  const currency = cleanCurrency(x.currency) ?? "LAK";
  const occurred = x.date_time ? parseLocalDateTime(x.date_time) : null;

  if (amount === null) reasons.push("Amount could not be read");
  if (!occurred) reasons.push("Date/time could not be read");
  if (!x.success) reasons.push("Receipt does not show a successful payment");

  const confidence = Number.isFinite(x.confidence) ? Math.min(1, Math.max(0, x.confidence)) : 0;
  if (confidence < CONFIDENCE_THRESHOLD) reasons.push("AI was not fully sure about this receipt");

  const transactionRef = cleanRef(x.transaction_ref);
  const ticketRef = cleanRef(x.ticket_ref);
  if (!transactionRef) reasons.push("No reference number found");

  const occurredAt = occurred ?? new Date();
  if (occurred && refMatchesDate(transactionRef, occurred) === false) {
    reasons.push("Reference number does not match the date");
  }

  const fromAccount = maskAccount(x.from_account_masked);
  const toAccount = maskAccount(x.recipient_account_masked);
  const toAmount = cleanAmount(x.to_amount);
  const toCurrency = cleanCurrency(x.to_currency);
  const rate = cleanAmount(x.exchange_rate);

  // Money moved between your own accounts is not spending.
  const sameName =
    !!x.from_name && !!x.recipient_name && normalizeName(x.from_name) === normalizeName(x.recipient_name);
  const ownHolder =
    !!x.recipient_name &&
    ctx.ownAccounts.some((o) => o.holder_name && normalizeName(o.holder_name) === normalizeName(x.recipient_name));
  const isOwnTransfer =
    x.receipt_type === "currency_exchange" || isOwnAccount(toAccount, ctx) || sameName || (ownHolder && !!toAccount);

  let amountLak: number | null = null;
  if (amount !== null) {
    if (currency === "LAK") amountLak = amount;
    else if (x.receipt_type === "currency_exchange" && toCurrency === "LAK" && toAmount !== null) amountLak = toAmount;
    else if (currency === "THB" && ctx.latestThbRate) amountLak = Math.round(amount * ctx.latestThbRate);
  }
  if (amountLak === null && amount !== null && !isOwnTransfer) {
    reasons.push(`Paid in ${currency}: please enter the kip amount`);
  }

  const counterparty = x.recipient_name?.trim() || null;

  return {
    kind: isOwnTransfer ? "own_transfer" : "expense",
    status: reasons.length ? "needs_review" : "confirmed",
    review_reasons: reasons,
    occurred_at: occurredAt.toISOString(),
    amount: amount ?? 0,
    currency,
    amount_lak: amountLak,
    fee: cleanAmount(x.fee),
    to_amount: toAmount,
    to_currency: toCurrency,
    exchange_rate: rate,
    receipt_type: x.receipt_type,
    counterparty_name: counterparty,
    counterparty_account: toAccount,
    from_account: fromAccount,
    transaction_ref: transactionRef,
    ticket_ref: ticketRef,
    dedupe_key: makeDedupeKey(amount ?? 0, currency, occurredAt, counterparty),
    memo: cleanMemo(x.memo),
    category: isOwnTransfer ? "other" : x.suggested_category,
    confidence,
  };
}

/** Kip per THB implied by an exchange receipt (THB -> LAK). */
export function thbRateFromExchange(d: TransactionDraft): number | null {
  if (d.receipt_type !== "currency_exchange") return null;
  if (d.currency === "THB" && d.to_currency === "LAK" && d.amount > 0 && d.to_amount) {
    return d.to_amount / d.amount;
  }
  if (d.currency === "LAK" && d.to_currency === "THB" && d.to_amount && d.to_amount > 0) {
    return d.amount / d.to_amount;
  }
  return null;
}
