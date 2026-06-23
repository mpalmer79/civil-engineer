import { documents } from "@/data/documents";
import StatusBadge from "@/components/StatusBadge";

export default function DocumentTable() {
  return (
    <div className="surface-card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
            <tr>
              <th scope="col" className="px-4 py-3">
                Document
              </th>
              <th scope="col" className="px-4 py-3">
                Type
              </th>
              <th scope="col" className="px-4 py-3">
                Status
              </th>
              <th scope="col" className="px-4 py-3">
                Purpose
              </th>
              <th scope="col" className="px-4 py-3">
                Expected key information
              </th>
              <th scope="col" className="px-4 py-3">
                Known issue / planted inconsistency
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {documents.map((doc) => (
              <tr key={doc.documentId} className="align-top hover:bg-slate-50">
                <td className="px-4 py-3">
                  <div className="font-medium text-slate-900">
                    {doc.fileName}
                  </div>
                  <div className="text-xs text-slate-400">{doc.documentId}</div>
                </td>
                <td className="px-4 py-3 text-slate-600">
                  {doc.documentType}
                </td>
                <td className="px-4 py-3">
                  <StatusBadge status={doc.status} />
                </td>
                <td className="px-4 py-3 text-slate-600">{doc.purpose}</td>
                <td className="px-4 py-3 text-slate-600">
                  {doc.expectedKeyInformation}
                </td>
                <td className="px-4 py-3">
                  {doc.knownIssue ? (
                    <span className="text-amber-700">{doc.knownIssue}</span>
                  ) : (
                    <span className="text-slate-400">—</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
