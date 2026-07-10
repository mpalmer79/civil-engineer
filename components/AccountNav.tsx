"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { getCurrentUser, logoutUser, type CurrentUser } from "@/lib/api";

// Client navigation control showing the signed-in user and a sign-out action,
// or a sign-in link when signed out. Reads the current user from the backend
// using the stored token.
export default function AccountNav() {
  const router = useRouter();
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    let active = true;
    getCurrentUser().then((u) => {
      if (active) {
        setUser(u);
        setLoaded(true);
      }
    });
    return () => {
      active = false;
    };
  }, []);

  const handleLogout = async () => {
    await logoutUser();
    setUser(null);
    router.push("/login");
    router.refresh();
  };

  if (!loaded) {
    return <span className="text-xs text-slate-400">...</span>;
  }

  if (!user) {
    return (
      <Link
        href="/login"
        className="rounded-md bg-water-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-water-700"
      >
        Sign in
      </Link>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <Link href="/me" className="nav-link" data-testid="account-link">
        {user.displayName}
      </Link>
      <button
        type="button"
        onClick={handleLogout}
        className="rounded-md border border-slate-300 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50"
      >
        Sign out
      </button>
    </div>
  );
}
