import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Kip Tracker",
  description: "Track your spending from BCEL One receipts",
  icons: { icon: "/icon-512.png", apple: "/apple-touch-icon.png" },
  appleWebApp: { capable: true, title: "Kip Tracker", statusBarStyle: "black-translucent" },
};

export const viewport: Viewport = {
  themeColor: "#b8121c",
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-dvh antialiased">
        <div className="liquid-bg" aria-hidden>
          <div className="blob blob-a" />
          <div className="blob blob-b" />
          <div className="blob blob-c" />
          <div className="blob blob-d" />
        </div>
        {children}
      </body>
    </html>
  );
}
