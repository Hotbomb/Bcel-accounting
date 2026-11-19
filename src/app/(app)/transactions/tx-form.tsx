"use client";
import { useActionState, useState } from "react";
import { CATEGORIES } from "@/lib/categories";
import type { FormState } from "../actions";

export interface TxFormValues {
  kind: "expense" | "income" | "own_transfer";
  amount: string;
  currency: string;
  amount_lak: string;
  occurred_at: string; // datetime-local value
  category: string;
  counterparty_name: string;
  memo: string;
}

export function TxForm({
  action,
  initial,
  submitLabel,
}: {
  action: (prev: FormState, data: FormData) => Promise<FormState>;
  initial: TxFormValues;
  submitLabel: string;
}) {
  const [state, formAction, pending] = useActionState(action, undefined);
  const [kind, setKind] = useState(initial.kind);
  const [currency, setCurrency] = useState(initial.currency);
  const cats = CATEGORIES.filter((c) => (kind === "income" ? c.kind === "income" : c.kind === "expense"));
  const [category, setCategory] = useState(cats.some((c) => c.slug === initial.category) ? initial.category : cats[0].slug);

  return (
    <form action={formAction} className="card space-y-4">
      <fieldset>
        <legend className="label">Type</legend>
        <div className="grid grid-cols-3 gap-2">
          {(
            [
              ["expense", "Spending"],
              ["income", "Income"],
              ["own_transfer", "Own transfer"],
            ] as const
          ).map(([value, label]) => (
            <label
              key={value}
              className={`cursor-pointer rounded-2xl px-2 py-3 text-center text-sm font-medium ring-1 ${
                kind === value ? "glass-red ring-0" : "bg-white/70 ring-white/80 hover:bg-white/90"
              }`}
            >
              <input
                type="radio"
                name="kind"
                value={value}
                checked={kind === value}
                onChange={() => {
                  setKind(value);
                  const next = CATEGORIES.filter((c) => (value === "income" ? c.kind === "income" : c.kind === "expense"));
                  if (!next.some((c) => c.slug === category)) setCategory(next[0].slug);
                }}
                className="sr-only"
              />
              {label}
            </label>
          ))}
        </div>
      </fieldset>

      <div className="grid grid-cols-[1fr_auto] gap-2">
        <div>
          <label className="label" htmlFor="amount">Amount</label>
          <input id="amount" name="amount" inputMode="decimal" required defaultValue={initial.amount} className="input text-lg font-semibold" placeholder="125,000" />
        </div>
        <div>
          <label className="label" htmlFor="currency">Currency</label>
          <select id="currency" name="currency" value={currency} onChange={(e) => setCurrency(e.target.value)} className="input">
            <option value="LAK">LAK ₭</option>
            <option value="THB">THB ฿</option>
            <option value="USD">USD $</option>
          </select>
        </div>
      </div>

      {currency !== "LAK" && (
        <div>
          <label className="label" htmlFor="amount_lak">Same amount in kip</label>
          <input id="amount_lak" name="amount_lak" inputMode="decimal" required defaultValue={initial.amount_lak} className="input" />
        </div>
      )}

      <div>
        <label className="label" htmlFor="occurred_at">Date and time</label>
        <input id="occurred_at" name="occurred_at" type="datetime-local" required defaultValue={initial.occurred_at} className="input" />
      </div>

      <div>
        <label className="label" htmlFor="category">Category</label>
        <select id="category" name="category" value={category} onChange={(e) => setCategory(e.target.value)} className="input">
          {cats.map((c) => (
            <option key={c.slug} value={c.slug}>
              {c.emoji} {c.en}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="label" htmlFor="counterparty_name">{kind === "income" ? "From (optional)" : "Paid to (optional)"}</label>
        <input id="counterparty_name" name="counterparty_name" defaultValue={initial.counterparty_name} maxLength={200} className="input" />
      </div>

      <div>
        <label className="label" htmlFor="memo">Note (optional)</label>
        <input id="memo" name="memo" defaultValue={initial.memo} maxLength={500} className="input" />
      </div>

      {state?.error && <p className="text-sm text-red-700" role="alert">{state.error}</p>}
      <button className="btn-primary w-full" disabled={pending}>
        {pending ? "Saving…" : submitLabel}
      </button>
    </form>
  );
}
