import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import SiteNav from "@/components/SiteNav";
import SiteFooter from "@/components/SiteFooter";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "Civil Engineer AI: Stormwater Review Assistant",
  description:
    "Review-support platform for stormwater plan review: DXF intake and metadata parsing, evidence traceability, review packets, a workflow board, response packages, resubmittal and revision comparison, and a reviewer command center. Reviewing the Brookside Meadows subdivision fixture.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="flex min-h-screen flex-col font-sans">
        <SiteNav />
        <main className="flex-1">{children}</main>
        <SiteFooter />
      </body>
    </html>
  );
}
