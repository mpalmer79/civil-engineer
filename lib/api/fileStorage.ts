import { API_BASE_URL, authHeaders, safeFetch } from "./client";

// Production Foundations Sprint 6: durable file storage. Document files are
// stored through a backend storage provider abstraction (local for development,
// S3-compatible object storage for deployment). The frontend never holds storage
// credentials and never sees raw filesystem paths. Protected routes include the
// Authorization header.
//
// NEXT_PUBLIC_API_BASE_URL is the backend origin only (no /api/v1 path); this
// client appends the /api/v1 paths itself.

export type DocumentStorageStatus = {
  documentId: string;
  projectId: string;
  fileAvailable: boolean;
  storageProvider: string | null;
  processingStatus: string | null;
  uploadStatus: string | null;
  contentType: string | null;
  fileSizeBytes: number | null;
  checksumSha256: string | null;
  originalFileName: string | null;
  uploadedAt: string | null;
  lastStorageCheckAt: string | null;
  downloadCount: number;
  lastDownloadedAt: string | null;
  message: string | null;
};

export type StorageHealth = {
  provider: string;
  configured: boolean;
  detail: string | null;
};

function mapStatus(s: Record<string, unknown>): DocumentStorageStatus {
  return {
    documentId: s.document_id as string,
    projectId: s.project_id as string,
    fileAvailable: (s.file_available as boolean) ?? false,
    storageProvider: (s.storage_provider as string) ?? null,
    processingStatus: (s.processing_status as string) ?? null,
    uploadStatus: (s.upload_status as string) ?? null,
    contentType: (s.content_type as string) ?? null,
    fileSizeBytes: (s.file_size_bytes as number) ?? null,
    checksumSha256: (s.checksum_sha256 as string) ?? null,
    originalFileName: (s.original_file_name as string) ?? null,
    uploadedAt: (s.uploaded_at as string) ?? null,
    lastStorageCheckAt: (s.last_storage_check_at as string) ?? null,
    downloadCount: (s.download_count as number) ?? 0,
    lastDownloadedAt: (s.last_downloaded_at as string) ?? null,
    message: (s.message as string) ?? null,
  };
}

export async function getDocumentStorageStatus(
  projectId: string,
  documentId: string,
): Promise<DocumentStorageStatus | null> {
  const data = await safeFetch<Record<string, unknown>>(
    `/api/v1/projects/${projectId}/documents/${documentId}/storage-status`,
  );
  return data ? mapStatus(data) : null;
}

export async function getStorageHealth(): Promise<StorageHealth | null> {
  const data = await safeFetch<Record<string, unknown>>("/api/v1/storage/health");
  if (!data) return null;
  return {
    provider: data.provider as string,
    configured: (data.configured as boolean) ?? false,
    detail: (data.detail as string) ?? null,
  };
}

type DownloadResult = {
  ok: boolean;
  backendReachable: boolean;
  error?: string;
};

// Download a document through the access-controlled backend route and trigger a
// browser save. The Authorization header is attached so protected files are
// available only to authorized users. The storage key and any signed URL stay
// on the backend.
export async function downloadDocument(
  projectId: string,
  documentId: string,
  fileName?: string,
): Promise<DownloadResult> {
  try {
    const res = await fetch(
      `${API_BASE_URL}/api/v1/projects/${projectId}/documents/${documentId}/download`,
      { headers: authHeaders(), cache: "no-store" },
    );
    if (!res.ok) {
      let detail = `Download failed (${res.status}).`;
      try {
        const parsed = (await res.json()) as { detail?: string };
        if (parsed.detail) detail = parsed.detail;
      } catch {
        // Keep the generic message.
      }
      return { ok: false, backendReachable: true, error: detail };
    }
    const blob = await res.blob();
    if (typeof window !== "undefined") {
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = fileName || "document";
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    }
    return { ok: true, backendReachable: true };
  } catch {
    return {
      ok: false,
      backendReachable: false,
      error: "Backend unavailable. Start the API to download files.",
    };
  }
}
