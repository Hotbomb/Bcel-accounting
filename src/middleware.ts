import { createServerClient } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";
import { supabaseConfigured, supabasePublishableKey, supabaseUrl } from "@/lib/env";

const PUBLIC_PATHS = ["/login", "/auth", "/pending", "/setup-check", "/manifest.webmanifest"];

export async function middleware(request: NextRequest) {
  const path = request.nextUrl.pathname;
  if (path === "/setup-check") return NextResponse.next();
  if (!supabaseConfigured()) return redirectToSetupCheck(request);
  try {
    return await handle(request);
  } catch {
    // Usually a mistyped Supabase setting. Show the setup check instead of crashing.
    return redirectToSetupCheck(request);
  }
}

function redirectToSetupCheck(request: NextRequest) {
  const url = request.nextUrl.clone();
  url.pathname = "/setup-check";
  url.search = "";
  return NextResponse.redirect(url);
}

async function handle(request: NextRequest) {

  let response = NextResponse.next({ request });
  const supabase = createServerClient(supabaseUrl(), supabasePublishableKey(), {
    cookies: {
      getAll: () => request.cookies.getAll(),
      setAll: (list) => {
        list.forEach(({ name, value }) => request.cookies.set(name, value));
        response = NextResponse.next({ request });
        list.forEach(({ name, value, options }) => response.cookies.set(name, value, options));
      },
    },
  });

  // Refreshes the sign-in session if needed.
  const {
    data: { user },
  } = await supabase.auth.getUser();

  const path = request.nextUrl.pathname;
  const isPublic = PUBLIC_PATHS.some((p) => path === p || path.startsWith(`${p}/`));
  if (!user && !isPublic) {
    if (path.startsWith("/api/")) return NextResponse.json({ error: "Please sign in." }, { status: 401 });
    const url = request.nextUrl.clone();
    url.pathname = "/login";
    return NextResponse.redirect(url);
  }
  return response;
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|.*\\.png$).*)"],
};
