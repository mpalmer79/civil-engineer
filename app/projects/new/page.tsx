import PageHeader from "@/components/PageHeader";
import ProjectIntakeForm from "@/components/ProjectIntakeForm";
import SignInNotice from "@/components/SignInNotice";

export default function NewProjectPage() {
  return (
    <div>
      <PageHeader
        eyebrow="Real project intake"
        title="New project"
        description="Create a real review-support project record. Brookside Meadows stays the seeded demo. This record requires human review and does not approve plans, certify compliance, or make engineering decisions."
      />
      <div className="mx-auto max-w-4xl space-y-6 px-4 py-10 sm:px-6 lg:px-8">
        <SignInNotice message="Sign in to create and own a real project record. When configured, project creation requires a signed-in user." />
        <ProjectIntakeForm />
      </div>
    </div>
  );
}
