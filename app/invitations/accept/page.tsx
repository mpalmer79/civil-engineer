import PageHeader from "@/components/PageHeader";
import AcceptInviteClient from "@/components/AcceptInviteClient";

export const dynamic = "force-dynamic";

export const metadata = {
  title: "Accept invitation",
};

export default async function AcceptInvitationPage(
  props: {
    searchParams: Promise<{ token?: string }>;
  }
) {
  const searchParams = await props.searchParams;
  return (
    <div>
      <PageHeader
        eyebrow="Workspace"
        title="Accept invitation"
        description="Join a Civil Engineer AI workspace you were invited to. Membership controls who can review records; it does not determine engineering outcomes."
      />
      <div className="mx-auto max-w-md space-y-4 px-4 py-10 sm:px-6 lg:px-8">
        <AcceptInviteClient token={searchParams.token ?? ""} />
      </div>
    </div>
  );
}
