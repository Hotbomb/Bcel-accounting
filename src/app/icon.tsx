import { ImageResponse } from "next/og";

export const size = { width: 512, height: 512 };
export const contentType = "image/png";

/** A "K" with a crossbar (like ₭), drawn with shapes so no font download is needed. */
export function kipMark(px: number) {
  return (
    <div style={{ width: "100%", height: "100%", display: "flex", background: "#0f766e" }}>
      <svg width={px} height={px} viewBox="0 0 512 512">
        <g stroke="white" strokeWidth="52" strokeLinecap="round" fill="none">
          <path d="M180 120 V392" />
          <path d="M360 120 L196 256 L360 392" strokeLinejoin="round" />
          <path d="M120 256 H392" strokeWidth="36" />
        </g>
      </svg>
    </div>
  );
}

export default function Icon() {
  return new ImageResponse(kipMark(512), size);
}
