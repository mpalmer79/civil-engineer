"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { registerUser } from "@/lib/api";

// Local registration form. Creates a user account and optionally a first
// organization (the new user becomes its org admin). Stores the returned access
// token client-side and routes to the account page.
export default function RegisterForm() {
  const router = useRouter();
  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [organizationName, setOrganizationName] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!displayName.trim() || !email.trim() || password.length < 8) {
      setError(
        "Enter a display name, a valid email, and a password of at least 8 characters.",
      );
      return;
    }
    setBusy(true);
    setError(null);
    const result = await registerUser({
      email: email.trim(),
      displayName: displayName.trim(),
      password,
      organizationName: organizationName.trim() || undefined,
    });
    setBusy(false);
    if (!result.ok || !result.data) {
      setError(result.error ?? "Registration failed.");
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
            Display name
          </label>
          <input
            type="text"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            className="form-input w-full"
          />
        </div>
        <div>
          <label className="form-label">
            Email
          </label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
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
            placeholder="At least 8 characters"
            className="form-input w-full"
          />
        </div>
        <div>
          <label className="form-label">
            Organization name (optional)
          </label>
          <input
            type="text"
            value={organizationName}
            onChange={(e) => setOrganizationName(e.target.value)}
            placeholder="Town of Riverton"
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
        {busy ? "Creating account..." : "Create account"}
      </button>

      <p className="mt-4 text-sm text-slate-600">
        Already have an account?{" "}
        <Link href="/login" className="text-water-700 hover:underline">
          Sign in
        </Link>
      </p>
    </div>
  );
}
