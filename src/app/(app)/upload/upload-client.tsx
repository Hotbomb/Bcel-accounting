"use client";
import Link from "next/link";
import { useRef, useState } from "react";
import { analyzePixels } from "@/lib/receipt/prefilter";

type Outcome = "added" | "needs_review" | "duplicate" | "not_receipt" | "filtered" | "error" | "limit";

interface Counts {
  added: number;
  needs_review: number;
  duplicate: number;
  skipped: number;
  error: number;
}

const EMPTY: Counts = { added: 0, needs_review: 0, duplicate: 0, skipped: 0, error: 0 };
const MAX_W = 1200;
const MAX_H = 2600;

async function sha256Hex(buf: ArrayBuffer): Promise<string> {
  const digest = await crypto.subtle.digest("SHA-256", buf);
  return [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

async function prepare(file: File, useFilter: boolean): Promise<{ skip: true } | { skip: false; blob: Blob; hash: string }> {
  const buf = await file.arrayBuffer();
  const hash = await sha256Hex(buf);
  const bitmap = await createImageBitmap(new Blob([buf], { type: file.type }));
  try {
    if (useFilter) {
      const w = 80;
      const h = Math.max(1, Math.round((bitmap.height * w) / bitmap.width));
      const small = document.createElement("canvas");
      small.width = w;
      small.height = h;
      const sctx = small.getContext("2d", { willReadFrequently: true })!;
      sctx.drawImage(bitmap, 0, 0, w, h);
      const verdict = analyzePixels(sctx.getImageData(0, 0, w, h).data, w, h).verdict;
      if (verdict === "unlikely") return { skip: true };
    }
    // Shrink before uploading: saves mobile data and stays under size limits.
    const scale = Math.min(1, MAX_W / bitmap.width, MAX_H / bitmap.height);
    const canvas = document.createElement("canvas");
    canvas.width = Math.round(bitmap.width * scale);
    canvas.height = Math.round(bitmap.height * scale);
    const ctx = canvas.getContext("2d")!;
    ctx.fillStyle = "#fff";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
    const blob = await new Promise<Blob>((resolve, reject) =>
      canvas.toBlob((b) => (b ? resolve(b) : reject(new Error("encode"))), "image/jpeg", 0.88),
    );
    return { skip: false, blob, hash };
  } finally {
    bitmap.close();
  }
}

async function send(blob: Blob, hash: string): Promise<{ outcome: Outcome; message?: string }> {
  const form = new FormData();
  form.append("image", blob, "receipt.jpg");
  form.append("hash", hash);
  try {
    const res = await fetch("/api/receipts", { method: "POST", body: form });
    const body = await res.json().catch(() => ({}));
    const r = body.result as string | undefined;
    if (r === "added" || r === "needs_review" || r === "duplicate" || r === "not_receipt" || r === "limit") {
      return { outcome: r, message: body.message };
    }
    return { outcome: "error", message: body.message };
  } catch {
    return { outcome: "error", message: "No connection" };
  }
}

export function UploadClient() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [useFilter, setUseFilter] = useState(true);
  const [running, setRunning] = useState(false);
  const [done, setDone] = useState(0);
  const [total, setTotal] = useState(0);
  const [counts, setCounts] = useState<Counts | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  async function handleFiles(list: FileList | null) {
    if (!list || list.length === 0) return;
    const files = [...list].filter((f) => f.type.startsWith("image/"));
    setRunning(true);
    setDone(0);
    setTotal(files.length);
    setNotice(null);
    const c: Counts = { ...EMPTY };
    setCounts({ ...c });
    let stop = false;

    const queue = [...files];
    const worker = async () => {
      while (queue.length && !stop) {
        const file = queue.shift()!;
        let outcome: Outcome;
        try {
          const p = await prepare(file, useFilter);
          if (p.skip) outcome = "filtered";
          else {
            const r = await send(p.blob, p.hash);
            outcome = r.outcome;
            if (r.outcome === "limit") {
              stop = true;
              setNotice(r.message ?? "Limit reached.");
            } else if (r.outcome === "error" && r.message) setNotice(r.message);
          }
        } catch {
          outcome = "error"; // e.g. a format this browser cannot open
        }
        if (outcome === "added") c.added++;
        else if (outcome === "needs_review") c.needs_review++;
        else if (outcome === "duplicate") c.duplicate++;
        else if (outcome === "not_receipt" || outcome === "filtered") c.skipped++;
        else if (outcome === "error") c.error++;
        setCounts({ ...c });
        setDone((d) => d + 1);
      }
    };
    await Promise.all([worker(), worker()]);
    setRunning(false);
    if (inputRef.current) inputRef.current.value = "";
  }

  const pct = total ? Math.round((done / total) * 100) : 0;

  return (
    <div className="space-y-4">
      <div className="card space-y-4">
        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          multiple
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />
        <button className="btn-primary w-full py-5 text-base" disabled={running} onClick={() => inputRef.current?.click()}>
          {running ? `Reading ${done} of ${total}…` : "Choose photos"}
        </button>
        <label className="flex items-start gap-3 text-sm text-ink/70">
          <input type="checkbox" className="mt-0.5 h-5 w-5 accent-brand" checked={useFilter} onChange={(e) => setUseFilter(e.target.checked)} disabled={running} />
          <span>
            Skip photos that clearly aren&apos;t BCEL receipts on this device first (recommended; saves AI costs). Turn off if a receipt was missed.
          </span>
        </label>
        {running && (
          <div className="h-2 overflow-hidden rounded-full bg-white/70" aria-hidden>
            <div className="h-full rounded-full bg-gradient-to-r from-brand to-gold transition-all" style={{ width: `${pct}%` }} />
          </div>
        )}
      </div>

      {counts && (
        <div className="card space-y-2" aria-live="polite">
          <p className="text-base font-semibold">
            {running ? "So far: " : ""}Added {counts.added + counts.needs_review} {counts.added + counts.needs_review === 1 ? "receipt" : "receipts"}, skipped{" "}
            {counts.skipped} other {counts.skipped === 1 ? "photo" : "photos"}
            {counts.duplicate ? `, ${counts.duplicate} already added` : ""}.
          </p>
          {counts.needs_review > 0 && (
            <p className="text-sm text-amber-800">
              {counts.needs_review} need a quick check.{" "}
              <Link href="/transactions?view=review" className="underline">
                Review now
              </Link>
            </p>
          )}
          {counts.error > 0 && <p className="text-sm text-red-700">{counts.error} could not be read. Try those again later.</p>}
          {notice && <p className="text-sm text-ink/70">{notice}</p>}
        </div>
      )}

      <p className="px-1 text-xs text-ink/60">
        Photos are only used to read the receipt and are deleted right away. Receipts that need checking are kept for up to 7 days so you can compare.
      </p>
    </div>
  );
}
