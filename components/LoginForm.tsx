"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { loginUser } from "@/lib/api";

// Local sign-in form. Submits email and password to the backend, stores the
// returned access token client-side, and routes to the account page. The token
// is never placed in a URL and never logged.
export default function LoginForm() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!email.trim() || !password) {
      setError("Enter your email and password.");
      return;
    }
    setBusy(true);
    setError(null);
    const result = await loginUser(email.trim(), password);
    setBusy(false);
    if (!result.ok || !result.data) {
      setError(result.error ?? "Sign in failed.");
      return;
    }
    router.push("/me");
    router.refresh();
  };

  return (
    <div className="surface-card p-6">
      <div className="space-y-3">
        <div>
          <label className="form-label">
            Email
          </label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="reviewer@example.com"
            className="form-input w-full"
          />
        </div>
        <div>
          <label className="form-label">
            Password
          </label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="form-input w-full"
          />
        </div>
      </div>

      {error ? (
        <p className="alert alert-danger mt-3">
          {error}
        </p>
      ) : null}

      <button
        type="button"
        onClick={handleSubmit}
        disabled={busy}
        className="btn btn-primary w-full mt-4"
      >
        {busy ? "Signing in..." : "Sign in"}
      </button>

      <p className="mt-4 text-sm text-slate-600">
        Need an account?{" "}
        <Link href="/register" className="text-water-700 hover:underline">
          Register
        </Link>
      </p>
      <p className="mt-1 text-sm text-slate-600">
        Forgot your password?{" "}
        <Link href="/reset-password" className="text-water-700 hover:underline">
          Reset it
        </Link>
      </p>
    </div>
  );
}
