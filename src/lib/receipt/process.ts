import "server-only";
import { createHash, randomUUID } from "node:crypto";
import type { SupabaseClient } from "@supabase/supabase-js";
import { monthKey } from "../time";
import { AllProvidersFailedError, extractReceipt } from "./extract";
import { normalizeExtraction, thbRateFromExchange, type OwnAccount } from "./normalize";
import type { ImageMediaType } from "./providers";
import { perUserLimit, recentCallCount, supabaseUsageStore, userReceiptCountThisMonth } from "./usage-store";

export const MAX_IMAGE_BYTES = 4 * 1024 * 1024;
export const ALLOWED_TYPES: ImageMediaType[] = ["image/jpeg", "image/png", "image/webp"];
const MAX_CALLS_PER_MINUTE = 30;
const REVIEW_IMAGE_DAYS = 7;

export type ProcessResult =
  | { result: "added"; transactionId: string; kind: string }
  | { result: "needs_review"; transactionId: string; reasons: string[] }
  | { result: "duplicate" }
  | { result: "not_receipt" }
  | { result: "limit"; message: string }
  | { result: "error"; message: string };

interface Input {
  supabase: SupabaseClient; // acting as the signed-in person (RLS applies)
  userId: string;
  monthlyLimit: number | null;
  bytes: Buffer;
  mediaType: ImageMediaType;
  /** Hash of the ORIGINAL photo computed on the device, if provided. */
  clientHash?: string | null;
}

export async function processReceiptImage({ supabase, userId, monthlyLimit, bytes, mediaType, clientHash }: Input): Promise<ProcessResult> {
  const hash = clientHash && /^[a-f0-9]{64}$/.test(clientHash) ? clientHash : createHash("sha256").update(bytes).digest("hex");

  // 1. Same photo seen before? Skip without calling the AI.
  const { data: seen } = await supabase.from("image_hashes").select("result").eq("sha256", hash).maybeSingle();
  if (seen) return seen.result === "not_receipt" ? { result: "not_receipt" } : { result: "duplicate" };

  // 2. Limits.
  if ((await recentCallCount(userId)) >= MAX_CALLS_PER_MINUTE) {
    return { result: "limit", message: "Too many photos at once. Wait a minute and try again." };
  }
  const month = monthKey();
  const limit = await perUserLimit(monthlyLimit);
  if ((await userReceiptCountThisMonth(userId, month)) >= limit) {
    return { result: "limit", message: `Monthly limit of ${limit} receipts reached.` };
  }

  // 3. Ask the AI.
  let outcome;
  try {
    outcome = await extractReceipt(bytes.toString("base64"), mediaType, supabaseUsageStore(userId));
  } catch (err) {
    if (err instanceof AllProvidersFailedError) return { result: "error", message: err.message };
    throw err;
  }

  // 4. Turn the answer into a transaction.
  const [{ data: accounts }, { data: lastExchange }] = await Promise.all([
    supabase.from("own_accounts").select("account_masked, holder_name"),
    supabase
      .from("transactions")
      .select("amount, currency, to_amount, to_currency, receipt_type")
      .eq("receipt_type", "currency_exchange")
      .order("occurred_at", { ascending: false })
      .limit(1)
      .maybeSingle(),
  ]);
  const latestThbRate = lastExchange
    ? thbRateFromExchange({
        receipt_type: "currency_exchange",
        amount: Number(lastExchange.amount),
        currency: lastExchange.currency,
        to_amount: lastExchange.to_amount === null ? null : Number(lastExchange.to_amount),
        to_currency: lastExchange.to_currency,
      } as Parameters<typeof thbRateFromExchange>[0])
    : null;

  const draft = normalizeExtraction(outcome.extraction, {
    ownAccounts: (accounts ?? []) as OwnAccount[],
    latestThbRate,
  });

  if (!draft) {
    await supabase.from("image_hashes").insert({ sha256: hash, result: "not_receipt" });
    return { result: "not_receipt" };
  }

  // 5. Learn the "from" account as one of yours.
  if (draft.from_account) {
    await supabase
      .from("own_accounts")
      .upsert(
        { account_masked: draft.from_account, holder_name: outcome.extraction.from_name, currency: draft.currency },
        { onConflict: "user_id,account_masked", ignoreDuplicates: true },
      );
  }

  // 6. Duplicates: same reference = definitely the same payment.
  if (draft.transaction_ref) {
    const { data: existing } = await supabase
      .from("transactions")
      .select("id")
      .eq("transaction_ref", draft.transaction_ref)
      .maybeSingle();
    if (existing) {
      await supabase.from("image_hashes").insert({ sha256: hash, result: "duplicate" });
      return { result: "duplicate" };
    }
  }
  // Same amount + minute + recipient might be a real second payment, so ask.
  const { data: similar } = await supabase.from("transactions").select("id").eq("dedupe_key", draft.dedupe_key).limit(1);
  if (similar && similar.length > 0) {
    draft.status = "needs_review";
    draft.review_reasons.push("Possible duplicate: same amount, time and recipient as another entry");
  }

  // 7. Save. Keep the image only if a person needs to check it.
  const id = randomUUID();
  let reviewImagePath: string | null = null;
  if (draft.status === "needs_review") {
    const ext = mediaType === "image/png" ? "png" : mediaType === "image/webp" ? "webp" : "jpg";
    reviewImagePath = `${userId}/${id}.${ext}`;
    const { error } = await supabase.storage.from("review-images").upload(reviewImagePath, bytes, { contentType: mediaType });
    if (error) reviewImagePath = null;
  }

  const { error } = await supabase.from("transactions").insert({
    id,
    ...draft,
    source: "receipt",
    extractor: outcome.extractor,
    review_image_path: reviewImagePath,
    review_image_expires_at: reviewImagePath ? new Date(Date.now() + REVIEW_IMAGE_DAYS * 86_400_000).toISOString() : null,
  });
  if (error) {
    if (reviewImagePath) await supabase.storage.from("review-images").remove([reviewImagePath]);
    if (error.code === "23505") return { result: "duplicate" }; // two uploads raced
    console.error("[process] insert failed", error.code);
    return { result: "error", message: "Could not save this receipt." };
  }
  await supabase.from("image_hashes").insert({ sha256: hash, result: "receipt" });

  return draft.status === "needs_review"
    ? { result: "needs_review", transactionId: id, reasons: draft.review_reasons }
    : { result: "added", transactionId: id, kind: draft.kind };
}
