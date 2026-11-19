import Link from "next/link";
import { notFound } from "next/navigation";
import { requireUser } from "@/lib/auth";
import { formatMoney } from "@/lib/money";
import { toLocalInputValue } from "@/lib/time";
import { deleteTransaction, updateTransaction } from "../../actions";
import { TxForm } from "../tx-form";

export const dynamic = "force-dynamic";

export default async function EditTransactionPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const { supabase } = await requireUser();
  const { data: t } = await supabase.from("transactions").select("*").eq("id", id).maybeSingle();
  if (!t) notFound();

  let imageUrl: string | null = null;
  if (t.review_image_path) {
    const { data } = await supabase.storage.from("review-images").createSignedUrl(t.review_image_path, 600);
    imageUrl = data?.signedUrl ?? null;
  }

  return (
    <main className="space-y-4">
      <Link href="/transactions" className="text-sm text-stone-500">← Transactions</Link>
      <h1 className="text-xl font-bold">{t.status === "needs_review" ? "Check this receipt" : "Edit transaction"}</h1>

      {t.status === "needs_review" && t.review_reasons?.length > 0 && (
        <ul className="card list-inside list-disc bg-amber-50 text-sm text-amber-900 ring-amber-200">
          {t.review_reasons.map((r: string) => (
            <li key={r}>{r}</li>
          ))}
        </ul>
      )}

      {imageUrl && (
        <details className="card" open>
          <summary className="cursor-pointer text-sm font-medium">Receipt image (deleted after you save, or in 7 days)</summary>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={imageUrl} alt="Receipt" className="mx-auto mt-3 max-h-[70vh] rounded-lg" />
        </details>
      )}

      {t.source === "receipt" && (
        <div className="card grid grid-cols-2 gap-2 text-sm text-stone-600">
          <span>From account</span>
          <span className="text-right">{t.from_account ?? "—"}</span>
          <span>To account</span>
          <span className="text-right">{t.counterparty_account ?? "—"}</span>
          <span>Reference</span>
          <span className="break-all text-right">{t.transaction_ref ?? "—"}</span>
          {t.receipt_type === "currency_exchange" && (
            <>
              <span>Exchanged</span>
              <span className="text-right">
                {formatMoney(Number(t.amount), t.currency)} → {formatMoney(Number(t.to_amount), t.to_currency ?? "LAK")}
              </span>
            </>
          )}
          <span>Read by</span>
          <span className="text-right">{t.extractor ?? "—"}</span>
        </div>
      )}

      <TxForm
        action={updateTransaction.bind(null, t.id)}
        submitLabel={t.status === "needs_review" ? "Looks right — save" : "Save changes"}
        initial={{
          kind: t.kind,
          amount: String(Number(t.amount)),
          currency: t.currency,
          amount_lak: t.amount_lak === null ? "" : String(Number(t.amount_lak)),
          occurred_at: toLocalInputValue(new Date(t.occurred_at)),
          category: t.category,
          counterparty_name: t.counterparty_name ?? "",
          memo: t.memo ?? "",
        }}
      />

      <form action={deleteTransaction.bind(null, t.id)}>
        <button className="btn-danger w-full">Delete this transaction</button>
      </form>
    </main>
  );
}
