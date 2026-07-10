import Link from "next/link";

import PageHeader from "@/components/PageHeader";
import DocumentRegisterForm from "@/components/DocumentRegisterForm";

export default async function RegisterDocumentPage(
  props: {
    params: Promise<{ projectId: string }>;
  }
) {
  const params = await props.params;
  return (
    <div>
      <PageHeader
        eyebrow="Real project intake"
        title="Register document"
        description="Register document metadata, or upload a document file, for this project record. Sprint 1 records intake metadata and stores uploaded files for review support. It does not parse, approve, or verify documents."
      />
      <div className="mx-auto max-w-4xl space-y-6 px-4 py-10 sm:px-6 lg:px-8">
        <Link href={`/projects/${params.projectId}/documents`} className="nav-link">
          Back to documents
        </Link>
        <DocumentRegisterForm projectId={params.projectId} />
      </div>
    </div>
  );
}
