import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { ALLOWED_TYPES, MAX_IMAGE_BYTES, processReceiptImage } from "@/lib/receipt/process";
import type { ImageMediaType } from "@/lib/receipt/providers";

export const runtime = "nodejs";
export const maxDuration = 60;

/** Upload ONE image. The browser sends photos one at a time. */
export async function POST(request: Request) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ result: "error", message: "Please sign in." }, { status: 401 });

  const { data: profile } = await supabase.from("profiles").select("approved, monthly_receipt_limit").eq("id", user.id).single();
  if (!profile?.approved) return NextResponse.json({ result: "error", message: "Account not approved." }, { status: 403 });

  let form: FormData;
  try {
    form = await request.formData();
  } catch {
    return NextResponse.json({ result: "error", message: "Bad upload." }, { status: 400 });
  }
  const file = form.get("image");
  if (!(file instanceof File)) return NextResponse.json({ result: "error", message: "No image." }, { status: 400 });
  if (!ALLOWED_TYPES.includes(file.type as ImageMediaType)) {
    return NextResponse.json({ result: "error", message: "Only JPEG, PNG or WebP images." }, { status: 415 });
  }
  if (file.size === 0 || file.size > MAX_IMAGE_BYTES) {
    return NextResponse.json({ result: "error", message: "Image too large (max 4 MB)." }, { status: 413 });
  }

  const bytes = Buffer.from(await file.arrayBuffer());
  const clientHash = typeof form.get("hash") === "string" ? (form.get("hash") as string) : null;

  try {
    const result = await processReceiptImage({
      supabase,
      userId: user.id,
      monthlyLimit: profile.monthly_receipt_limit,
      bytes,
      mediaType: file.type as ImageMediaType,
      clientHash,
    });
    const status = result.result === "limit" ? 429 : result.result === "error" ? 502 : 200;
    return NextResponse.json(result, { status });
  } catch {
    console.error("[api/receipts] unexpected failure");
    return NextResponse.json({ result: "error", message: "Something went wrong." }, { status: 500 });
  }
  // The image only ever lived in memory for this request (unless it needs review).
}
