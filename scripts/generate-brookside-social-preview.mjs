#!/usr/bin/env node
// Deterministic generator for the Brookside Meadows social preview image.
//
// Reads the committed conceptual aerial (never modified) and produces the
// 1200x630 LinkedIn / Open Graph derivative:
//
//   source  public/images/civil-engineer/brookside-project-thumbnail.webp (1672x941)
//   output  public/images/civil-engineer/brookside-social-preview.webp   (1200x630)
//
// Crop decision: the source is 16:9 (1672x941) and the target is 40:21
// (1200x630), so the derivative must lose vertical content. The crop keeps
// the full width detail that matters (a centered 1640x861 window anchored to
// the bottom edge), which preserves the stormwater pond, the surrounding
// subdivision, and the lower-left Brookside title block while trimming only
// sky and treeline from the top. No text overlay is added.
//
// The same input, options, and sharp version produce byte-identical output,
// so the derivative can be regenerated and diffed in CI. Run through:
//   npm run media:generate

import { existsSync } from "node:fs";
import { stat } from "node:fs/promises";
import path from "node:path";
import process from "node:process";

import sharp from "sharp";

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const SOURCE = path.join(
  ROOT,
  "public/images/civil-engineer/brookside-project-thumbnail.webp",
);
const OUTPUT = path.join(
  ROOT,
  "public/images/civil-engineer/brookside-social-preview.webp",
);

const TARGET = { width: 1200, height: 630 };
// Largest 40:21 window inside 1672x941 with integer edges: 1640x861.
// Centered horizontally ((1672 - 1640) / 2 = 16) and anchored to the bottom
// (941 - 861 = 80) to keep the lower-left Brookside title area.
const CROP = { left: 16, top: 80, width: 1640, height: 861 };
const MAX_BYTES = 350 * 1024;

async function main() {
  if (!existsSync(SOURCE)) {
    console.error(`Source image missing: ${SOURCE}`);
    process.exit(1);
  }

  const meta = await sharp(SOURCE).metadata();
  if (meta.width !== 1672 || meta.height !== 941) {
    console.error(
      `Source dimensions changed (expected 1672x941, found ${meta.width}x${meta.height}). ` +
        "Update the crop constants deliberately before regenerating.",
    );
    process.exit(1);
  }

  await sharp(SOURCE)
    .extract(CROP)
    .resize(TARGET.width, TARGET.height)
    .webp({ quality: 82, effort: 6 })
    .toFile(OUTPUT);

  const { size } = await stat(OUTPUT);
  console.log(
    `Wrote ${path.relative(ROOT, OUTPUT)} (${TARGET.width}x${TARGET.height}, ${size} bytes)`,
  );
  if (size > MAX_BYTES) {
    console.error(
      `Social preview is ${size} bytes, above the documented ${MAX_BYTES}-byte limit. ` +
        "Lower the WebP quality setting and regenerate.",
    );
    process.exit(1);
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
