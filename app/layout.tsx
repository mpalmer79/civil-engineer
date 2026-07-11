import type { Metadata } from "next";
import "./globals.css";
import SiteNav from "@/components/SiteNav";
import SiteFooter from "@/components/SiteFooter";
import CivilEngineerAIGuide from "@/components/CivilEngineerAIGuide";
import {
  DEFAULT_DESCRIPTION,
  DEFAULT_TITLE,
  pageMetadata,
} from "@/lib/pageMetadata";
import { siteUrl } from "@/lib/siteUrl";

// Site-wide metadata defaults. metadataBase makes every relative image and
// canonical path resolve to an absolute HTTPS URL on the configured origin
// (NEXT_PUBLIC_SITE_URL, falling back to the deployed Railway frontend).
// Pages override title, description, and canonical for their own route
// through the same pageMetadata helper; the Brookside social preview is the
// default link-preview image everywhere.
export const metadata: Metadata = {
  metadataBase: new URL(siteUrl()),
  ...pageMetadata({
    title: DEFAULT_TITLE,
    description: DEFAULT_DESCRIPTION,
    path: "/",
  }),
  // Canonical URLs are a per-page decision. Without this removal, every
  // page that does not export its own metadata would inherit a canonical
  // of "/" from the layout.
  alternates: undefined,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="flex min-h-screen flex-col font-sans">
        <SiteNav />
        <main className="flex-1">{children}</main>
        <SiteFooter />
        <CivilEngineerAIGuide />
      </body>
    </html>
  );
}
