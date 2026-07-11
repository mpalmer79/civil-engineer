// Canonical site origin for absolute URLs in metadata.
//
// NEXT_PUBLIC_SITE_URL overrides the default when the frontend is served from
// a different origin (for example a custom domain). It must be the origin
// only, with no trailing path. When unset, the deployed Railway frontend
// origin from the README is used so social previews always resolve to an
// absolute HTTPS URL, even in local production builds.

const PRODUCTION_SITE_URL = "https://civil-engineer.up.railway.app";

export function siteUrl(): string {
  const configured = process.env.NEXT_PUBLIC_SITE_URL?.trim();
  const origin = configured || PRODUCTION_SITE_URL;
  return origin.replace(/\/+$/, "");
}

export function absoluteUrl(path: string): string {
  return `${siteUrl()}${path.startsWith("/") ? path : `/${path}`}`;
}
