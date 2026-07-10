import type { Metadata } from "next";
import "./globals.css";
import SiteNav from "@/components/SiteNav";
import SiteFooter from "@/components/SiteFooter";
import CivilEngineerAIGuide from "@/components/CivilEngineerAIGuide";

export const metadata: Metadata = {
  title: "Civil Engineer AI: Stormwater Review Assistant",
  description:
    "Document-first, evidence-first, reviewer-controlled stormwater review-support platform for municipal and civil engineering plan review. Real project records, document storage, PDF page indexing, evidence citations and retrieval, checklist review, applicant response matrix, resubmittal rounds, and reviewer response packages. Brookside Meadows is the public guided demo fixture.",
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
