import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Kip Tracker",
    short_name: "Kip",
    description: "Track your spending from BCEL One receipts",
    start_url: "/",
    display: "standalone",
    background_color: "#fbf3f1",
    theme_color: "#b8121c",
    icons: [
      { src: "/icon", sizes: "512x512", type: "image/png" },
      { src: "/apple-icon", sizes: "180x180", type: "image/png" },
    ],
  };
}
