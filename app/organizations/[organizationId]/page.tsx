import OrganizationPageClient from "./Client";

// Server wrapper: unwraps the async route params (Next.js 15) and renders the
// client page body with a plain prop, keeping hooks and data loading in the
// client component.
export default async function OrganizationDetailPage(props: {
  params: Promise<{ organizationId: string }>;
}) {
  const { organizationId } = await props.params;
  return <OrganizationPageClient organizationId={organizationId} />;
}
