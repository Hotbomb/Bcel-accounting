import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Kip Tracker",
    short_name: "Kip",
    description: "Track your spending from BCEL One receipts",
    start_url: "/",
    display: "standalone",
    background_color: "#f5f6f4",
    theme_color: "#0f766e",
    icons: [
      { src: "/icon", sizes: "512x512", type: "image/png" },
      { src: "/apple-icon", sizes: "180x180", type: "image/png" },
    ],
  };
}
