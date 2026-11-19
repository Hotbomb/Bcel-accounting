"use server";

import { redirect } from "next/navigation";
import { revalidatePath } from "next/cache";
import { z } from "zod";
import { CATEGORIES } from "@/lib/categories";
import { parseAmountInput } from "@/lib/money";
import { createClient } from "@/lib/supabase/server";
import { parseLocalDateTime } from "@/lib/time";

export async function signOut() {
  const supabase = await createClient();
  await supabase.auth.signOut();
  redirect("/login");
}

const FormSchema = z.object({
  kind: z.enum(["expense", "income", "own_transfer"]),
  amount: z.string(),
  currency: z.enum(["LAK", "THB", "USD"]),
  amount_lak: z.string().optional(),
  occurred_at: z.string(),
  category: z.string().refine((s) => CATEGORIES.some((c) => c.slug === s), "Unknown category"),
  counterparty_name: z.string().max(200).optional(),
  memo: z.string().max(500).optional(),
});

function readForm(formData: FormData) {
  const raw = Object.fromEntries(
    ["kind", "amount", "currency", "amount_lak", "occurred_at", "category", "counterparty_name", "memo"].map((k) => [
      k,
      (formData.get(k) as string | null) ?? undefined,
    ]),
  );
  const parsed = FormSchema.safeParse(raw);
  if (!parsed.success) return { error: "Please check the form." } as const;
  const f = parsed.data;
  const amount = parseAmountInput(f.amount);
  if (amount === null || amount <= 0) return { error: "Enter a valid amount." } as const;
  const occurred = parseLocalDateTime(f.occurred_at);
  if (!occurred) return { error: "Enter a valid date and time." } as const;
  let amountLak: number | null = f.currency === "LAK" ? amount : null;
  if (f.currency !== "LAK") {
    amountLak = f.amount_lak ? parseAmountInput(f.amount_lak) : null;
    if (amountLak === null) return { error: "Enter the amount in kip as well." } as const;
  }
  return {
    values: {
      kind: f.kind,
      amount,
      currency: f.currency,
      amount_lak: amountLak,
      occurred_at: occurred.toISOString(),
      category: f.category,
      counterparty_name: f.counterparty_name?.trim() || null,
      memo: f.memo?.trim() || null,
    },
  } as const;
}

export type FormState = { error?: string } | undefined;

export async function createManualTransaction(_prev: FormState, formData: FormData): Promise<FormState> {
  const r = readForm(formData);
  if ("error" in r) return { error: r.error };
  const supabase = await createClient();
  const { error } = await supabase.from("transactions").insert({ ...r.values, source: "manual", status: "confirmed" });
  if (error) return { error: "Could not save. Please try again." };
  revalidatePath("/", "layout");
  redirect("/transactions");
}

async function deleteReviewImage(supabase: Awaited<ReturnType<typeof createClient>>, id: string) {
  const { data } = await supabase.from("transactions").select("review_image_path").eq("id", id).single();
  if (data?.review_image_path) await supabase.storage.from("review-images").remove([data.review_image_path]);
}

/** Save edits. Saving also confirms the item and deletes its review image. */
export async function updateTransaction(id: string, _prev: FormState, formData: FormData): Promise<FormState> {
  const r = readForm(formData);
  if ("error" in r) return { error: r.error };
  const supabase = await createClient();
  await deleteReviewImage(supabase, id);
  const { error } = await supabase
    .from("transactions")
    .update({ ...r.values, status: "confirmed", review_reasons: [], review_image_path: null, review_image_expires_at: null })
    .eq("id", id);
  if (error) return { error: "Could not save. Please try again." };
  revalidatePath("/", "layout");
  redirect("/transactions");
}

export async function confirmTransaction(id: string) {
  const supabase = await createClient();
  const { data } = await supabase.from("transactions").select("amount_lak, kind").eq("id", id).single();
  if (data && data.amount_lak === null && data.kind !== "own_transfer") redirect(`/transactions/${id}`);
  await deleteReviewImage(supabase, id);
  await supabase
    .from("transactions")
    .update({ status: "confirmed", review_reasons: [], review_image_path: null, review_image_expires_at: null })
    .eq("id", id);
  revalidatePath("/", "layout");
}

export async function deleteTransaction(id: string) {
  const supabase = await createClient();
  await deleteReviewImage(supabase, id);
  await supabase.from("transactions").delete().eq("id", id);
  revalidatePath("/", "layout");
  redirect("/transactions");
}
