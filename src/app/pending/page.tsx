import { signOut } from "../(app)/actions";

export default function PendingPage() {
  return (
    <main className="mx-auto flex min-h-dvh max-w-sm flex-col justify-center px-6 text-center">
      <h1 className="text-xl font-bold">Waiting for approval</h1>
      <p className="mt-3 text-stone-600">
        You are signed in, but this app is invite only. Ask the admin to approve your account, then sign in again.
      </p>
      <form action={signOut} className="mt-6">
        <button className="btn-secondary w-full">Sign out</button>
      </form>
    </main>
  );
}
