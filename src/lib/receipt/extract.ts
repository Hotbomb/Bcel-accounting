import { estimateCostUsd } from "../cost";
import { monthKey } from "../time";
import {
  ProviderError,
  extractWithClaude,
  extractWithGemini,
  type ImageMediaType,
  type ProviderResult,
} from "./providers";
import type { Extraction } from "./schema";

export interface UsageRecord {
  provider: "anthropic" | "gemini";
  model: string;
  inputTokens: number;
  outputTokens: number;
  costUsd: number;
  success: boolean;
  errorKind: string | null;
  usageMonth: string;
}

/** Storage for AI usage and the monthly cap (backed by Supabase in production). */
export interface UsageStore {
  claudeSpentThisMonth(month: string): Promise<number>;
  claudeCapUsd(): Promise<number>;
  claudePausedMonth(): Promise<string | null>;
  pauseClaude(month: string): Promise<void>;
  record(usage: UsageRecord): Promise<void>;
}

export interface Providers {
  claude: (b64: string, type: ImageMediaType) => Promise<ProviderResult>;
  gemini: (b64: string, type: ImageMediaType) => Promise<ProviderResult>;
}

const defaultProviders: Providers = { claude: extractWithClaude, gemini: extractWithGemini };

export interface ExtractOutcome {
  extraction: Extraction;
  extractor: string; // e.g. "anthropic:claude-haiku-5-5"
}

export class AllProvidersFailedError extends Error {}

/**
 * Read one image. Uses Claude unless it is paused (credit ran out) or this
 * month's cap is reached; otherwise, or if Claude fails, uses Gemini. Claude
 * comes back automatically next month because the pause is tied to a month.
 */
export async function extractReceipt(
  imageBase64: string,
  mediaType: ImageMediaType,
  store: UsageStore,
  providers: Providers = defaultProviders,
  now: Date = new Date(),
): Promise<ExtractOutcome> {
  const month = monthKey(now);

  let useClaude = true;
  if ((await store.claudePausedMonth()) === month) useClaude = false;
  else if ((await store.claudeSpentThisMonth(month)) >= (await store.claudeCapUsd())) useClaude = false;

  const attempts: Array<["anthropic" | "gemini", Providers["claude"]]> = useClaude
    ? [
        ["anthropic", providers.claude],
        ["gemini", providers.gemini],
      ]
    : [["gemini", providers.gemini]];

  for (const [provider, call] of attempts) {
    try {
      const result = await call(imageBase64, mediaType);
      await store.record({
        provider,
        model: result.model,
        inputTokens: result.inputTokens,
        outputTokens: result.outputTokens,
        costUsd: estimateCostUsd(provider, result.model, result.inputTokens, result.outputTokens),
        success: true,
        errorKind: null,
        usageMonth: month,
      });
      return { extraction: result.extraction, extractor: `${provider}:${result.model}` };
    } catch (err) {
      const pe = err instanceof ProviderError ? err : new ProviderError("other", "unknown error");
      if (provider === "anthropic" && pe.kind === "out_of_credit") await store.pauseClaude(month);
      await store.record({
        provider,
        model: provider,
        inputTokens: pe.inputTokens,
        outputTokens: pe.outputTokens,
        costUsd: estimateCostUsd(provider, provider === "anthropic" ? "claude-haiku-5-5" : "gemini", pe.inputTokens, pe.outputTokens),
        success: false,
        errorKind: pe.kind,
        usageMonth: month,
      });
      // Log the kind only - never image content or personal data.
      console.warn(`[extract] ${provider} failed: ${pe.kind}`);
    }
  }
  throw new AllProvidersFailedError("Could not read this image right now. Please try again later.");
}
