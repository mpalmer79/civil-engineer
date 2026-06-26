import PageHeader from "@/components/PageHeader";
import LoginForm from "@/components/LoginForm";

export const dynamic = "force-dynamic";

export default function LoginPage() {
  return (
    <div>
      <PageHeader
        eyebrow="Account"
        title="Sign in"
        description="Sign in to access your organization's real project review records. The public Brookside Meadows demo remains available without an account."
      />
      <div className="mx-auto max-w-md space-y-4 px-4 py-10 sm:px-6 lg:px-8">
        <LoginForm />
        <p className="rounded-md bg-slate-50 px-3 py-2 text-xs text-slate-500">
          Local demo accounts (development only, change before real use):
          reviewer@example.com / demo-reviewer-pass and admin@example.com /
          demo-admin-pass.
        </p>
      </div>
    </div>
  );
}
