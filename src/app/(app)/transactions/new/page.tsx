import { requireUser } from "@/lib/auth";
import { toLocalInputValue } from "@/lib/time";
import { createManualTransaction } from "../../actions";
import { TxForm } from "../tx-form";

export default async function NewTransactionPage({ searchParams }: { searchParams: Promise<{ kind?: string }> }) {
  await requireUser();
  const { kind } = await searchParams;
  return (
    <main className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold text-white">Manual entry</h1>
        <p className="mt-1 text-sm text-white/90">For income, cash spending, or anything without a BCEL receipt.</p>
      </div>
      <TxForm
        action={createManualTransaction}
        submitLabel="Save"
        initial={{
          kind: kind === "expense" ? "expense" : "income",
          amount: "",
          currency: "LAK",
          amount_lak: "",
          occurred_at: toLocalInputValue(new Date()),
          category: kind === "expense" ? "food" : "salary",
          counterparty_name: "",
          memo: "",
        }}
      />
    </main>
  );
}
