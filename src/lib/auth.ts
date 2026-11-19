import "server-only";
import { redirect } from "next/navigation";
import { createClient } from "./supabase/server";

export interface Profile {
  id: string;
  email: string;
  display_name: string | null;
  role: "admin" | "member";
  approved: boolean;
  monthly_receipt_limit: number | null;
}

/** For pages: returns the signed-in, approved person or redirects. */
export async function requireUser() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) redirect("/login");
  const { data: profile } = await supabase.from("profiles").select("*").eq("id", user.id).single<Profile>();
  if (!profile || !profile.approved) redirect("/pending");
  return { supabase, user, profile };
}
