import { describe, expect, it } from "vitest";
import { cleanMemo, maskAccount, normalizeExtraction, normalizeName, thbRateFromExchange } from "@/lib/receipt/normalize";
import { notReceipt, ownExchange, qrPayment, transferToPerson } from "./fixtures";

const ctx = { ownAccounts: [], latestThbRate: null };

describe("normalizeExtraction", () => {
  it("turns a transfer to another person into confirmed spending", () => {
    const d = normalizeExtraction(transferToPerson, ctx)!;
    expect(d.kind).toBe("expense");
    expect(d.status).toBe("confirmed");
    expect(d.amount_lak).toBe(290000);
    expect(d.memo).toBeNull(); // "." means empty
    expect(d.occurred_at).toBe("2026-11-18T13:40:19.000Z"); // 20:40 in Vientiane = 13:40 UTC
    expect(d.counterparty_name).toBe("BOUNMY EXAMPLE MR");
  });

  it("marks a THB->LAK exchange between own accounts as an own transfer, not spending", () => {
    const d = normalizeExtraction(ownExchange, ctx)!;
    expect(d.kind).toBe("own_transfer");
    expect(d.status).toBe("confirmed");
    expect(d.amount_lak).toBe(333340);
    expect(thbRateFromExchange(d)).toBeCloseTo(666.68, 2);
  });

  it("treats a transfer to a known own account as an own transfer", () => {
    const d = normalizeExtraction(
      { ...transferToPerson, recipient_name: "SOMEONE", recipient_account_masked: "222-12-xxxxx999" },
      { ownAccounts: [{ account_masked: "222-12-xxxxx999", holder_name: null }], latestThbRate: null },
    )!;
    expect(d.kind).toBe("own_transfer");
  });

  it("reads a QR shop payment and strips spaces from the reference", () => {
    const d = normalizeExtraction(qrPayment, ctx)!;
    expect(d.kind).toBe("expense");
    expect(d.transaction_ref).toBe("202611124436407");
    expect(d.category).toBe("food");
    expect(d.status).toBe("confirmed");
  });

  it("returns null for non-receipts", () => {
    expect(normalizeExtraction(notReceipt, ctx)).toBeNull();
  });

  it("sends low-confidence receipts to review", () => {
    const d = normalizeExtraction({ ...transferToPerson, confidence: 0.5 }, ctx)!;
    expect(d.status).toBe("needs_review");
    expect(d.review_reasons.join()).toMatch(/not fully sure/);
  });

  it("sends receipts whose reference date disagrees with the printed date to review", () => {
    const d = normalizeExtraction({ ...transferToPerson, date_time: "2026-11-19T20:40:19" }, ctx)!;
    expect(d.status).toBe("needs_review");
  });

  it("converts THB spending with the latest exchange rate, or asks when unknown", () => {
    const thb = { ...transferToPerson, amount: 100, currency: "THB" };
    expect(normalizeExtraction(thb, { ownAccounts: [], latestThbRate: 666.68 })!.amount_lak).toBe(66668);
    const unknown = normalizeExtraction(thb, ctx)!;
    expect(unknown.amount_lak).toBeNull();
    expect(unknown.status).toBe("needs_review");
  });

  it("rejects impossible dates", () => {
    const d = normalizeExtraction({ ...transferToPerson, date_time: "2026-02-31T10:00:00" }, ctx)!;
    expect(d.status).toBe("needs_review");
  });
});

describe("helpers", () => {
  it("masks long digit runs but keeps already-masked accounts", () => {
    expect(maskAccount("222-12-xxxxx254")).toBe("222-12-xxxxx254");
    expect(maskAccount("2221234567254")).toBe("xxxxxxxxxx254");
  });
  it("compares names ignoring titles and spacing", () => {
    expect(normalizeName("Martin Phetsomphou MR")).toBe(normalizeName("MARTIN  PHETSOMPHOU"));
  });
  it("cleans memos", () => {
    expect(cleanMemo(" . ")).toBeNull();
    expect(cleanMemo("lunch")).toBe("lunch");
  });
});
