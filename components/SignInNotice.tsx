"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { isSignedIn } from "@/lib/api";

// Small client-side notice prompting sign-in for real project actions while
// making clear the public Brookside Meadows demo stays available without an
// account. Renders nothing once a signed-in session is detected.
export default function SignInNotice({
  message,
}: {
  message?: string;
}) {
  const [signedIn, setSignedIn] = useState<boolean | null>(null);

  useEffect(() => {
    setSignedIn(isSignedIn());
  }, []);

  if (signedIn) return null;

  return (
    <div className="rounded-lg border border-water-200 bg-water-50 px-4 py-3 text-sm text-water-800">
      <p>
        {message ??
          "Sign in to view and manage real project review records. The public Brookside Meadows demo remains available without an account."}{" "}
        <Link href="/login" className="font-semibold underline">
          Sign in
        </Link>{" "}
        or{" "}
        <Link href="/register" className="font-semibold underline">
          create an account
        </Link>
        .
      </p>
    </div>
  );
}
