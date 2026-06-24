"use client";

import { useEffect, useState } from "react";
import {
  getResponsePackagePrintView,
  type ResponsePackagePrintView,
} from "@/lib/api";
import HumanReviewSignoffChecklist from "@/components/HumanReviewSignoffChecklist";
import ResponseAttachmentChecklist from "@/components/ResponseAttachmentChecklist";

// A printable draft preview of the response letter or memo, assembled from the
// backend print view. It is clearly labeled draft external communication
// support and is not a final or issued response.
export default function ResponsePackagePrintPreview({
  packageId,
}: {
  packageId: string;
}) {
  const [view, setView] = useState<ResponsePackagePrintView | null>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    (async () => {
      setView(await getResponsePackagePrintView(packageId));
      setLoaded(true);
    })();
  }, [packageId]);

  if (!loaded) {
    return (
      <div className="surface-card p-6 text-sm text-slate-500">
        Loading printable draft...
      </div>
    );
  }
  if (!view) {
    return (
      <div className="surface-card p-6 text-sm text-slate-500">
        The printable draft is not available. Start the backend to load it.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3">
        <p className="text-sm font-semibold text-amber-800">{view.draftNotice}</p>
      </div>

      <article className="surface-card space-y-4 p-8">
        <header>
          <h2 className="text-xl font-bold text-slate-900">{view.title}</h2>
          <p className="mt-1 text-sm text-slate-500">
            Audience: {view.audienceType.replace(/_/g, " ")} · Status:{" "}
            {view.status.replace(/_/g, " ")}
          </p>
        </header>

        <p className="text-sm text-slate-700">{view.draftIntro}</p>

        {view.sections.map((section) => (
          <section key={section.title}>
            <h3 className="text-base font-semibold text-slate-900">
              {section.title}
            </h3>
            <p className="mt-1 text-xs text-slate-500">{section.summary}</p>
            <ol className="mt-2 list-decimal space-y-2 pl-5">
              {section.items.map((item) => (
                <li key={item.itemId} className="text-sm text-slate-700">
                  {item.draftText}
                </li>
              ))}
            </ol>
          </section>
        ))}

        <p className="text-sm text-slate-700">{view.draftClosing}</p>

        <footer className="border-t border-slate-200 pt-4">
          <p className="text-xs text-slate-500">{view.limitationsNote}</p>
          <p className="mt-2 text-xs text-slate-500">
            {view.externalCommunicationBoundary}
          </p>
        </footer>
      </article>

      <ResponseAttachmentChecklist attachments={view.attachments} />
      <HumanReviewSignoffChecklist items={view.signoffChecklist} />
    </div>
  );
}
