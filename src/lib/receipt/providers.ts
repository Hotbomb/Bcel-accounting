import Anthropic from "@anthropic-ai/sdk";
import { zodOutputFormat } from "@anthropic-ai/sdk/helpers/zod";
import { GoogleGenAI, createPartFromBase64 } from "@google/genai";
import { CLAUDE_MODEL, GEMINI_MODEL } from "../cost";
import { SYSTEM_PROMPT, USER_INSTRUCTION } from "./prompt";
import { ExtractionSchema, extractionJsonSchema, type Extraction } from "./schema";

export type ImageMediaType = "image/jpeg" | "image/png" | "image/webp";

export interface ProviderResult {
  extraction: Extraction;
  model: string;
  inputTokens: number;
  outputTokens: number;
}

/** Why a provider failed. "out_of_credit" pauses Claude for the rest of the month. */
export type ProviderErrorKind = "out_of_credit" | "auth" | "rate_limited" | "server" | "refused" | "invalid_output" | "not_configured" | "other";

export class ProviderError extends Error {
  constructor(
    public kind: ProviderErrorKind,
    message: string,
    public inputTokens = 0,
    public outputTokens = 0,
  ) {
    super(message);
  }
}

let anthropic: Anthropic | null = null;
let gemini: GoogleGenAI | null = null;

export async function extractWithClaude(imageBase64: string, mediaType: ImageMediaType): Promise<ProviderResult> {
  if (!process.env.ANTHROPIC_API_KEY) throw new ProviderError("not_configured", "ANTHROPIC_API_KEY is not set");
  anthropic ??= new Anthropic({ maxRetries: 1, timeout: 45_000 });

  let response;
  try {
    response = await anthropic.messages.parse({
      model: CLAUDE_MODEL,
      max_tokens: 4000,
      system: SYSTEM_PROMPT,
      output_config: { effort: "low", format: zodOutputFormat(ExtractionSchema) },
      messages: [
        {
          role: "user",
          content: [
            { type: "image", source: { type: "base64", media_type: mediaType, data: imageBase64 } },
            { type: "text", text: USER_INSTRUCTION },
          ],
        },
      ],
    });
  } catch (err) {
    throw classifyAnthropicError(err);
  }

  const inputTokens = response.usage.input_tokens + (response.usage.cache_read_input_tokens ?? 0);
  const outputTokens = response.usage.output_tokens;
  if (response.stop_reason === "refusal") {
    throw new ProviderError("refused", "Claude declined this image", inputTokens, outputTokens);
  }
  const parsed = response.parsed_output;
  if (!parsed) throw new ProviderError("invalid_output", "Claude returned no valid JSON", inputTokens, outputTokens);
  // Validate again ourselves - never trust the shape blindly.
  const checked = ExtractionSchema.safeParse(parsed);
  if (!checked.success) throw new ProviderError("invalid_output", "Claude JSON failed validation", inputTokens, outputTokens);
  return { extraction: checked.data, model: CLAUDE_MODEL, inputTokens, outputTokens };
}

function classifyAnthropicError(err: unknown): ProviderError {
  if (err instanceof Anthropic.PaymentRequiredError) return new ProviderError("out_of_credit", "Claude credit exhausted");
  if (err instanceof Anthropic.BadRequestError && /credit balance|billing/i.test(err.message)) {
    return new ProviderError("out_of_credit", "Claude credit exhausted");
  }
  if (err instanceof Anthropic.AuthenticationError || err instanceof Anthropic.PermissionDeniedError) {
    return new ProviderError("auth", "Claude key rejected");
  }
  if (err instanceof Anthropic.RateLimitError) return new ProviderError("rate_limited", "Claude rate limited");
  if (err instanceof Anthropic.InternalServerError || err instanceof Anthropic.APIConnectionError) {
    return new ProviderError("server", "Claude unavailable");
  }
  if (err instanceof Anthropic.APIError) return new ProviderError("other", `Claude error ${err.status ?? ""}`.trim());
  return new ProviderError("other", "Claude call failed");
}

export async function extractWithGemini(imageBase64: string, mediaType: ImageMediaType): Promise<ProviderResult> {
  if (!process.env.GEMINI_API_KEY) throw new ProviderError("not_configured", "GEMINI_API_KEY is not set");
  gemini ??= new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });

  let response;
  try {
    response = await gemini.models.generateContent({
      model: GEMINI_MODEL,
      contents: [
        {
          role: "user",
          parts: [createPartFromBase64(imageBase64, mediaType), { text: USER_INSTRUCTION }],
        },
      ],
      config: {
        systemInstruction: SYSTEM_PROMPT,
        responseMimeType: "application/json",
        responseJsonSchema: extractionJsonSchema,
        maxOutputTokens: 4000,
      },
    });
  } catch (err) {
    const status = (err as { status?: number })?.status;
    if (status === 429) throw new ProviderError("rate_limited", "Gemini rate limited (free tier limit?)");
    if (status === 401 || status === 403) throw new ProviderError("auth", "Gemini key rejected");
    if (status && status >= 500) throw new ProviderError("server", "Gemini unavailable");
    throw new ProviderError("other", "Gemini call failed");
  }

  const usage = response.usageMetadata;
  const inputTokens = usage?.promptTokenCount ?? 0;
  const outputTokens = (usage?.candidatesTokenCount ?? 0) + (usage?.thoughtsTokenCount ?? 0);
  let json: unknown;
  try {
    json = JSON.parse(response.text ?? "");
  } catch {
    throw new ProviderError("invalid_output", "Gemini returned no valid JSON", inputTokens, outputTokens);
  }
  const checked = ExtractionSchema.safeParse(json);
  if (!checked.success) throw new ProviderError("invalid_output", "Gemini JSON failed validation", inputTokens, outputTokens);
  return { extraction: checked.data, model: GEMINI_MODEL, inputTokens, outputTokens };
}
