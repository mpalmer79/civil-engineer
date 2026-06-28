"use client";

import { useState } from "react";
import Link from "next/link";

import { confirmPasswordReset } from "@/lib/api";

// Password reset confirmation form. Takes the reset token (from the link query),
// collects a new password, and confirms it with the backend. On success it links
// to sign-in. The token is never displayed or logged.
export default function PasswordResetConfirmForm({ token }: { token: string }) {
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!token) {
    return (
      <div className="surface-card p-6">
        <p className="alert alert-danger">
          This reset link is missing its token. Request a new reset link.
        </p>
        <Link
          href="/reset-password"
          className="mt-4 inline-block font-semibold text-water-700 hover:underline"
        >
          Request a new link →
        </Link>
      </div>
    );
  }

  const handleSubmit = async () => {
    if (password.length < 8) {
      setError("Use a password of at least 8 characters.");
      return;
    }
    if (password !== confirm) {
      setError("The passwords do not match.");
      return;
    }
    setBusy(true);
    setError(null);
    const result = await confirmPasswordReset(token, password);
    setBusy(false);
    if (!result.ok || !result.data) {
      setError(result.error ?? "Could not reset the password.");
      return;
    }
    setDone(true);
  };

  if (done) {
    return (
      <div className="surface-card p-6">
        <p className="alert alert-success">
          Your password has been reset. Sign in with your new password.
        </p>
        <Link href="/login" className="btn btn-primary mt-4">
          Sign in
        </Link>
      </div>
    );
  }

  return (
    <div className="surface-card p-6">
      <div className="space-y-3">
        <div>
          <label className="form-label">New password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="form-input w-full"
          />
        </div>
        <div>
          <label className="form-label">Confirm new password</label>
          <input
            type="password"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            className="form-input w-full"
          />
        </div>
      </div>

      {error ? <p className="alert alert-danger mt-3">{error}</p> : null}

      <button
        type="button"
        onClick={handleSubmit}
        disabled={busy}
        className="btn btn-primary w-full mt-4"
      >
        {busy ? "Saving..." : "Set new password"}
      </button>
    </div>
  );
}
