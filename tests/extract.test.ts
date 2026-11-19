import { describe, expect, it, vi } from "vitest";
import { extractReceipt, type UsageRecord, type UsageStore } from "@/lib/receipt/extract";
import { ProviderError, type ProviderResult } from "@/lib/receipt/providers";
import { transferToPerson } from "./fixtures";

function store(opts: { spent?: number; cap?: number; paused?: string | null } = {}) {
  const records: UsageRecord[] = [];
  let paused = opts.paused ?? null;
  const s: UsageStore & { records: UsageRecord[]; paused: () => string | null } = {
    records,
    paused: () => paused,
    claudeSpentThisMonth: async () => opts.spent ?? 0,
    claudeCapUsd: async () => opts.cap ?? 5,
    claudePausedMonth: async () => paused,
    pauseClaude: async (m) => {
      paused = m;
    },
    record: async (u) => {
      records.push(u);
    },
  };
  return s;
}

const ok = (model: string): ProviderResult => ({ extraction: transferToPerson, model, inputTokens: 3000, outputTokens: 300 });
const NOW = new Date("2026-11-19T05:00:00Z");

describe("extractReceipt fallback", () => {
  it("uses Claude first and records its estimated cost", async () => {
    const s = store();
    const gemini = vi.fn();
    const r = await extractReceipt("x", "image/jpeg", s, { claude: async () => ok("claude-haiku-5-5"), gemini }, NOW);
    expect(r.extractor).toBe("anthropic:claude-haiku-5-5");
    expect(gemini).not.toHaveBeenCalled();
    expect(s.records[0].costUsd).toBeCloseTo((3000 * 0.1 + 300 * 0.5) / 1e6, 10);
  });

  it("falls back to Gemini when Claude errors", async () => {
    const s = store();
    const r = await extractReceipt(
      "x",
      "image/jpeg",
      s,
      {
        claude: async () => {
          throw new ProviderError("server", "down");
        },
        gemini: async () => ok("gemini-3.8-flash"),
      },
      NOW,
    );
    expect(r.extractor).toBe("gemini:gemini-3.8-flash");
    expect(s.records.map((x) => x.success)).toEqual([false, true]);
  });

  it("pauses Claude for the month when credit runs out", async () => {
    const s = store();
    await extractReceipt(
      "x",
      "image/jpeg",
      s,
      {
        claude: async () => {
          throw new ProviderError("out_of_credit", "no credit");
        },
        gemini: async () => ok("g"),
      },
      NOW,
    );
    expect(s.paused()).toBe("2026-11");
  });

  it("skips Claude when paused this month or over the cap, and uses it again next month", async () => {
    const claude = vi.fn(async () => ok("c"));
    const gemini = vi.fn(async () => ok("g"));
    await extractReceipt("x", "image/jpeg", store({ paused: "2026-11" }), { claude, gemini }, NOW);
    await extractReceipt("x", "image/jpeg", store({ spent: 5.01, cap: 5 }), { claude, gemini }, NOW);
    expect(claude).not.toHaveBeenCalled();
    expect(gemini).toHaveBeenCalledTimes(2);
    await extractReceipt("x", "image/jpeg", store({ paused: "2026-11" }), { claude, gemini }, new Date("2026-12-01T01:00:00Z"));
    expect(claude).toHaveBeenCalledTimes(1);
  });

  it("throws a friendly error when both fail", async () => {
    const fail = async () => {
      throw new ProviderError("server", "down");
    };
    await expect(extractReceipt("x", "image/jpeg", store(), { claude: fail, gemini: fail }, NOW)).rejects.toThrow(/try again/);
  });
});
