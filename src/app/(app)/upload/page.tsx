import { UploadClient } from "./upload-client";

export default function UploadPage() {
  return (
    <main className="space-y-4">
      <div>
        <h1 className="text-xl font-bold">Add receipts</h1>
        <p className="mt-1 text-sm text-stone-600">
          Select as many photos as you like, even your whole recent gallery. Other photos and receipts you already added are skipped automatically.
        </p>
      </div>
      <UploadClient />
    </main>
  );
}
