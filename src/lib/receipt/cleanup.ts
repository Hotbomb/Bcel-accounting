import "server-only";
import type { SupabaseClient } from "@supabase/supabase-js";

/**
 * Deletes this person's review images that are past their 7-day limit.
 * Runs whenever they open the home screen (no scheduled job needed).
 */
export async function deleteExpiredReviewImages(supabase: SupabaseClient): Promise<void> {
  try {
    const { data } = await supabase
      .from("transactions")
      .select("id, review_image_path")
      .not("review_image_path", "is", null)
      .lt("review_image_expires_at", new Date().toISOString())
      .limit(50);
    const rows = data ?? [];
    if (!rows.length) return;
    await supabase.storage.from("review-images").remove(rows.map((r) => r.review_image_path as string));
    await supabase
      .from("transactions")
      .update({ review_image_path: null, review_image_expires_at: null })
      .in(
        "id",
        rows.map((r) => r.id),
      );
  } catch {
    // Never block the page for housekeeping.
  }
}
