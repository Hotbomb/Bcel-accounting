import { z } from "zod";
import { EXPENSE_CATEGORY_SLUGS } from "../categories";

// What we ask the AI to return for every image. Kept simple (no min/max) so it
// works with strict structured output on both Claude and Gemini; the stricter
// checks happen in normalize.ts.
export const ExtractionSchema = z.object({
  is_bcel_receipt: z.boolean(),
  receipt_type: z.enum(["transfer", "qr_payment", "currency_exchange", "other"]),
  success: z.boolean(),
  date_time: z.string().nullable(),
  amount: z.number().nullable(),
  currency: z.string().nullable(),
  to_amount: z.number().nullable(),
  to_currency: z.string().nullable(),
  exchange_rate: z.number().nullable(),
  fee: z.number().nullable(),
  from_name: z.string().nullable(),
  from_account_masked: z.string().nullable(),
  recipient_name: z.string().nullable(),
  recipient_account_masked: z.string().nullable(),
  transaction_ref: z.string().nullable(),
  ticket_ref: z.string().nullable(),
  memo: z.string().nullable(),
  suggested_category: z.enum(EXPENSE_CATEGORY_SLUGS),
  confidence: z.number(),
});

export type Extraction = z.infer<typeof ExtractionSchema>;

/** Plain JSON Schema version, used for Gemini (without the "$schema" marker). */
const { $schema: _ignored, ...jsonSchema } = z.toJSONSchema(ExtractionSchema) as Record<string, unknown>;
void _ignored;
export const extractionJsonSchema = jsonSchema;
