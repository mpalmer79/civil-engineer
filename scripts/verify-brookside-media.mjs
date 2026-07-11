#!/usr/bin/env node
// Verification gate for the Brookside Meadows media set.
//
// Checks, without any external dependency:
//   1. The source aerial exists, is a valid WebP, and is 1672x941.
//   2. The social preview exists, is a valid WebP, and is exactly 1200x630.
//   3. The social preview is within the documented file-size limit (350 KB).
//   4. Every image path referenced by lib/brooksideMedia.ts exists in public/.
//   5. The dimensions declared in lib/brooksideMedia.ts match the real files.
//
// Run through: npm run media:verify

import { existsSync, readFileSync, statSync } from "node:fs";
import path from "node:path";
import process from "node:process";

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const MEDIA_MODULE = path.join(ROOT, "lib/brooksideMedia.ts");
const SOURCE = "/images/civil-engineer/brookside-project-thumbnail.webp";
const SOCIAL = "/images/civil-engineer/brookside-social-preview.webp";
const MAX_SOCIAL_BYTES = 350 * 1024;

const failures = [];
function check(ok, label, detail) {
  const status = ok ? "ok" : "fail";
  console.log(`[${status}] ${label}: ${detail}`);
  if (!ok) failures.push(label);
}

// Minimal WebP header parser covering the three container layouts (lossy
// VP8, lossless VP8L, extended VP8X). Returns null for anything that is not
// a structurally valid WebP.
function webpInfo(buffer) {
  if (buffer.length < 30) return null;
  if (buffer.toString("ascii", 0, 4) !== "RIFF") return null;
  if (buffer.toString("ascii", 8, 12) !== "WEBP") return null;
  const chunk = buffer.toString("ascii", 12, 16);
  if (chunk === "VP8 ") {
    // Lossy bitstream: start code 9d 01 2a, then 14-bit width and height.
    if (buffer[23] !== 0x9d || buffer[24] !== 0x01 || buffer[25] !== 0x2a) {
      return null;
    }
    return {
      format: "VP8 (lossy)",
      width: buffer.readUInt16LE(26) & 0x3fff,
      height: buffer.readUInt16LE(28) & 0x3fff,
    };
  }
  if (chunk === "VP8L") {
    if (buffer[20] !== 0x2f) return null;
    const bits = buffer.readUInt32LE(21);
    return {
      format: "VP8L (lossless)",
      width: (bits & 0x3fff) + 1,
      height: ((bits >> 14) & 0x3fff) + 1,
    };
  }
  if (chunk === "VP8X") {
    return {
      format: "VP8X (extended)",
      width: 1 + ((buffer[26] << 16) | (buffer[25] << 8) | buffer[24]),
      height: 1 + ((buffer[29] << 16) | (buffer[28] << 8) | buffer[27]),
    };
  }
  return null;
}

function verifyImage(publicPath, expected) {
  const filePath = path.join(ROOT, "public", publicPath);
  if (!existsSync(filePath)) {
    check(false, publicPath, "file is missing");
    return;
  }
  const info = webpInfo(readFileSync(filePath));
  check(info !== null, `${publicPath} format`, info ? info.format : "not a valid WebP");
  if (!info) return;
  check(
    info.width === expected.width && info.height === expected.height,
    `${publicPath} dimensions`,
    `${info.width}x${info.height} (expected ${expected.width}x${expected.height})`,
  );
  const { size } = statSync(filePath);
  if (expected.maxBytes) {
    check(
      size <= expected.maxBytes,
      `${publicPath} size`,
      `${size} bytes (limit ${expected.maxBytes})`,
    );
  } else {
    console.log(`[info] ${publicPath} size: ${size} bytes`);
  }
}

verifyImage(SOURCE, { width: 1672, height: 941 });
verifyImage(SOCIAL, { width: 1200, height: 630, maxBytes: MAX_SOCIAL_BYTES });

// Every /images/... path referenced by the media module must exist, and the
// declared dimensions must match the files verified above.
const moduleSource = readFileSync(MEDIA_MODULE, "utf8");
const referencedPaths = [...moduleSource.matchAll(/"(\/images\/[^"]+)"/g)].map(
  (m) => m[1],
);
check(
  referencedPaths.length >= 2,
  "brooksideMedia references",
  `${referencedPaths.length} image paths declared`,
);
for (const ref of referencedPaths) {
  check(
    existsSync(path.join(ROOT, "public", ref)),
    `referenced path ${ref}`,
    "exists in public/",
  );
}
check(
  moduleSource.includes("width: 1672") && moduleSource.includes("height: 941"),
  "declared source dimensions",
  "lib/brooksideMedia.ts declares 1672x941 for the source image",
);
check(
  moduleSource.includes("width: 1200") && moduleSource.includes("height: 630"),
  "declared social dimensions",
  "lib/brooksideMedia.ts declares 1200x630 for the social preview",
);

if (failures.length > 0) {
  console.error(`\nBrookside media verification failed (${failures.length}).`);
  process.exit(1);
}
console.log("\nBrookside media verification passed.");
