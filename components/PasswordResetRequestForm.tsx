"use client";

import { useState } from "react";
import Link from "next/link";

import { requestPasswordReset } from "@/lib/api";

// Password reset request form. Submits an email and shows a uniform confirmation
// that never reveals whether an account exists. Outside production the backend
// also returns a dev token so the reset link can be followed locally without an
// email provider; that link is clearly labeled development only.
export default function PasswordResetRequestForm() {
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [devToken, setDevToken] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!email.trim()) {
      setError("Enter your email.");
      return;
    }
    setBusy(true);
    setError(null);
    setMessage(null);
    setDevToken(null);
    const result = await requestPasswordReset(email.trim());
    setBusy(false);
    if (!result.ok || !result.data) {
      setError(result.error ?? "Could not request a reset.");
      return;
    }
    setMessage(result.data.detail);
    setDevToken(result.data.devResetToken);
  };

  return (
    <div className="surface-card p-6">
      <div>
        <label className="form-label">Email</label>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@example.com"
          className="form-input w-full"
        />
      </div>

      {error ? <p className="alert alert-danger mt-3">{error}</p> : null}
      {message ? <p className="alert alert-info mt-3">{message}</p> : null}

      {devToken ? (
        <div className="alert alert-warning mt-3 text-sm">
          <p className="font-semibold">Development only</p>
          <p>
            No email provider is configured, so this reset link is shown here for
            local testing. It is never shown in production.
          </p>
          <Link
            href={`/reset-password/confirm?token=${encodeURIComponent(devToken)}`}
            className="mt-2 inline-block font-semibold text-water-700 hover:underline"
          >
            Continue to set a new password →
          </Link>
        </div>
      ) : null}

      <button
        type="button"
        onClick={handleSubmit}
        disabled={busy}
        className="btn btn-primary w-full mt-4"
      >
        {busy ? "Sending..." : "Send reset link"}
      </button>

      <p className="mt-4 text-sm text-slate-600">
        Remembered it?{" "}
        <Link href="/login" className="text-water-700 hover:underline">
          Sign in
        </Link>
      </p>
    </div>
  );
}
