import { NextResponse } from "next/server";
import { createAdminClient } from "@/lib/supabase/admin";

export const runtime = "nodejs";

/** Runs daily (see vercel.json): deletes review images older than 7 days. */
export async function GET(request: Request) {
  const secret = process.env.CRON_SECRET;
  if (!secret || request.headers.get("authorization") !== `Bearer ${secret}`) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }
  const db = createAdminClient();
  const { data } = await db
    .from("transactions")
    .select("id, review_image_path")
    .not("review_image_path", "is", null)
    .lt("review_image_expires_at", new Date().toISOString())
    .limit(500);
  const rows = data ?? [];
  if (rows.length) {
    await db.storage.from("review-images").remove(rows.map((r) => r.review_image_path as string));
    await db
      .from("transactions")
      .update({ review_image_path: null, review_image_expires_at: null })
      .in(
        "id",
        rows.map((r) => r.id),
      );
  }
  return NextResponse.json({ deleted: rows.length });
}
