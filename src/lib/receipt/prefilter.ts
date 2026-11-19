// A cheap, local check that runs BEFORE any AI call. BCEL One receipts have a
// solid BCEL-red band at the top and at the bottom with a white card between.
// This is deliberately cautious: when unsure it says "maybe" and the image is
// sent to the AI, because missing a real receipt is worse than a tiny cost.

export interface PrefilterResult {
  verdict: "likely" | "maybe" | "unlikely";
  reason: string;
  topRed: number;
  bottomRed: number;
  redShare: number;
}

/** BCEL red is roughly rgb(185, 18, 28). Accept a generous range around it. */
export function isBcelRed(r: number, g: number, b: number): boolean {
  return r >= 140 && g <= 80 && b <= 90 && r - g >= 90 && r - b >= 80;
}

/**
 * @param data RGBA pixels (e.g. from canvas getImageData), small is fine (~80px wide)
 */
export function analyzePixels(data: Uint8ClampedArray | Uint8Array, width: number, height: number): PrefilterResult {
  const rowRed = new Array<number>(height).fill(0);
  let totalRed = 0;
  for (let y = 0; y < height; y++) {
    let red = 0;
    for (let x = 0; x < width; x++) {
      const i = (y * width + x) * 4;
      if (isBcelRed(data[i], data[i + 1], data[i + 2])) red++;
    }
    rowRed[y] = red / width;
    totalRed += red;
  }
  const redShare = totalRed / (width * height);

  // Best "mostly red" row in the top quarter and in the bottom quarter. Using
  // a quarter (not just the edge) still works for screenshots that include
  // the phone's status bar above the receipt.
  const quarter = Math.max(1, Math.floor(height / 4));
  const topRed = Math.max(...rowRed.slice(0, quarter));
  const bottomRed = Math.max(...rowRed.slice(height - quarter));

  const aspect = height / width;
  const base = { topRed, bottomRed, redShare };

  if (topRed >= 0.6 && bottomRed >= 0.6 && redShare >= 0.05 && redShare <= 0.6) {
    return { verdict: "likely", reason: "BCEL red bands found", ...base };
  }
  if (aspect < 0.9 || aspect > 3.2) {
    return { verdict: "unlikely", reason: "Shape does not match a receipt", ...base };
  }
  if (topRed < 0.15 && bottomRed < 0.15 && redShare < 0.02) {
    return { verdict: "unlikely", reason: "No BCEL red found", ...base };
  }
  return { verdict: "maybe", reason: "Some red found; letting the AI decide", ...base };
}
