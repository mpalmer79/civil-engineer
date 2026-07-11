import PageHeader from "@/components/PageHeader";
import PasswordResetConfirmForm from "@/components/PasswordResetConfirmForm";

export const dynamic = "force-dynamic";

export const metadata = {
  title: "Set a new password",
};

export default async function ResetPasswordConfirmPage(
  props: {
    searchParams: Promise<{ token?: string }>;
  }
) {
  const searchParams = await props.searchParams;
  return (
    <div>
      <PageHeader
        eyebrow="Account"
        title="Set a new password"
        description="Choose a new password to finish resetting your account."
      />
      <div className="mx-auto max-w-md space-y-4 px-4 py-10 sm:px-6 lg:px-8">
        <PasswordResetConfirmForm token={searchParams.token ?? ""} />
      </div>
    </div>
  );
}
