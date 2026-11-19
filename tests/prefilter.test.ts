import { describe, expect, it } from "vitest";
import { analyzePixels } from "@/lib/receipt/prefilter";

const RED = [185, 18, 28];
const WHITE = [245, 245, 245];

function image(width: number, height: number, colorAt: (x: number, y: number) => number[]) {
  const data = new Uint8ClampedArray(width * height * 4);
  for (let y = 0; y < height; y++)
    for (let x = 0; x < width; x++) {
      const [r, g, b] = colorAt(x, y);
      const i = (y * width + x) * 4;
      data[i] = r;
      data[i + 1] = g;
      data[i + 2] = b;
      data[i + 3] = 255;
    }
  return data;
}

describe("analyzePixels", () => {
  it("recognises a receipt layout: red top and bottom bands around a white card", () => {
    const w = 60,
      h = 100;
    const data = image(w, h, (x, y) => (y < 11 || y > 93 || x < 2 || x > 57 ? RED : WHITE));
    expect(analyzePixels(data, w, h).verdict).toBe("likely");
  });

  it("still recognises a screenshot with a black status bar above the receipt", () => {
    const w = 60,
      h = 120;
    const data = image(w, h, (_x, y) => (y < 8 ? [0, 0, 0] : y < 20 || y > 110 ? RED : WHITE));
    expect(analyzePixels(data, w, h).verdict).toBe("likely");
  });

  it("rejects an ordinary landscape photo", () => {
    const data = image(100, 60, (x, y) => [(x * 2) % 255, (y * 3) % 255, 120]);
    expect(analyzePixels(data, 100, 60).verdict).toBe("unlikely");
  });

  it("rejects a portrait image with no red at all", () => {
    const data = image(60, 100, () => [40, 120, 200]);
    expect(analyzePixels(data, 60, 100).verdict).toBe("unlikely");
  });

  it("says maybe for a red-ish portrait image it cannot be sure about", () => {
    const data = image(60, 100, (_x, y) => (y < 10 ? RED : WHITE));
    expect(analyzePixels(data, 60, 100).verdict).toBe("maybe");
  });
});
