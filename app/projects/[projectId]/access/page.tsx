import ProjectAccessPageClient from "./Client";

// Server wrapper: unwraps the async route params (Next.js 15) and renders the
// client page body with a plain prop, keeping hooks and data loading in the
// client component.
export default async function ProjectAccessPage(props: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await props.params;
  return <ProjectAccessPageClient projectId={projectId} />;
}
