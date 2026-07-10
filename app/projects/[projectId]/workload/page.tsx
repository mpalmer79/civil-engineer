import ProjectWorkloadPageClient from "./Client";

// Server wrapper: unwraps the async route params (Next.js 15) and renders the
// client page body with a plain prop, keeping hooks and data loading in the
// client component.
export default async function ProjectWorkloadPage(props: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await props.params;
  return <ProjectWorkloadPageClient projectId={projectId} />;
}
