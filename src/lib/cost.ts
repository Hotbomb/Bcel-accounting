// Estimated prices in US dollars per million tokens. These are estimates for
// the cost cap; your real bill is in the Anthropic / Google consoles.
export const CLAUDE_MODEL = process.env.CLAUDE_MODEL || "claude-haiku-5-5";
export const GEMINI_MODEL = process.env.GEMINI_MODEL || "gemini-3.8-flash";

const PRICES: Record<string, { input: number; output: number }> = {
  // Claude Haiku 5.5: $0.10 in / $0.50 out for prompts up to 100K tokens.
  "claude-haiku-5-5": { input: 0.1, output: 0.5 },
};

function envPrice(name: string): number | undefined {
  const v = process.env[name];
  if (v === undefined || v === "") return undefined;
  const n = Number(v);
  return Number.isFinite(n) && n >= 0 ? n : undefined;
}

export function estimateCostUsd(
  provider: "anthropic" | "gemini",
  model: string,
  inputTokens: number,
  outputTokens: number,
): number {
  let price: { input: number; output: number };
  if (provider === "gemini") {
    // Free tier by default. Set GEMINI_INPUT_PRICE / GEMINI_OUTPUT_PRICE if you move to paid.
    price = { input: envPrice("GEMINI_INPUT_PRICE") ?? 0, output: envPrice("GEMINI_OUTPUT_PRICE") ?? 0 };
  } else {
    price = PRICES[model] ?? {
      input: envPrice("CLAUDE_INPUT_PRICE") ?? 0.1,
      output: envPrice("CLAUDE_OUTPUT_PRICE") ?? 0.5,
    };
  }
  return (inputTokens * price.input + outputTokens * price.output) / 1_000_000;
}
