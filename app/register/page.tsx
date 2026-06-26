import PageHeader from "@/components/PageHeader";
import RegisterForm from "@/components/RegisterForm";

export const dynamic = "force-dynamic";

export default function RegisterPage() {
  return (
    <div>
      <PageHeader
        eyebrow="Account"
        title="Create an account"
        description="Create a local account to manage real project review records. You can optionally create your organization now and become its admin."
      />
      <div className="mx-auto max-w-md px-4 py-10 sm:px-6 lg:px-8">
        <RegisterForm />
      </div>
    </div>
  );
}
