import PageHeader from "@/components/PageHeader";
import PasswordResetRequestForm from "@/components/PasswordResetRequestForm";

export const dynamic = "force-dynamic";

export const metadata = {
  title: "Reset password",
};

export default function ResetPasswordPage() {
  return (
    <div>
      <PageHeader
        eyebrow="Account"
        title="Reset your password"
        description="Enter your email and we will issue a reset link. For your security, the same confirmation is shown whether or not an account exists."
      />
      <div className="mx-auto max-w-md space-y-4 px-4 py-10 sm:px-6 lg:px-8">
        <PasswordResetRequestForm />
      </div>
    </div>
  );
}
