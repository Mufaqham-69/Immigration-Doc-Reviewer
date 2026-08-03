"use client";

import { useCallback, useEffect, useState } from "react";
import { api, type Case, type DocumentDetail } from "@/lib/api";
import { StatusStamp } from "@/components/StatusStamp";
import { FlagsList } from "@/components/FlagsList";
import { UploadDropzone } from "@/components/UploadDropzone";

export default function CaseDetailPage({ params }: { params: { id: string } }) {
  const [caseData, setCaseData] = useState<Case | null>(null);
  const [documents, setDocuments] = useState<DocumentDetail[]>([]);

  const refresh = useCallback(async () => {
    const [c, docs] = await Promise.all([api.getCase(params.id), api.listDocuments(params.id)]);
    setCaseData(c);
    setDocuments(docs);
  }, [params.id]);

  useEffect(() => {
    refresh();
    // Poll while documents are still processing - OCR/extraction runs async in Celery.
    const interval = setInterval(refresh, 5000);
    return () => clearInterval(interval);
  }, [refresh]);

  if (!caseData) return <main className="max-w-4xl mx-auto px-6 py-12 text-ink/50">Loading case…</main>;

  const summary = caseData.eligibility_summary;

  return (
    <main className="max-w-4xl mx-auto px-6 py-12">
      <div className="flex items-start justify-between mb-8">
        <div>
          <p className="font-mono text-xs text-ink/50 mb-1">#{caseData.id.slice(0, 8)}</p>
          <h1 className="font-display text-3xl">{caseData.visa_category}</h1>
        </div>
        {summary && <StatusStamp status={summary.overall_readiness} />}
      </div>

      <section className="mb-10">
        <UploadDropzone
          onUpload={async (file) => {
            await api.uploadDocument(params.id, file);
            await refresh();
          }}
        />
      </section>

      <section className="mb-10">
        <h2 className="font-display text-xl mb-3">Documents</h2>
        {documents.length === 0 ? (
          <p className="text-sm text-ink/50">No documents uploaded yet.</p>
        ) : (
          <ul className="space-y-2">
            {documents.map((doc) => (
              <li
                key={doc.id}
                className="bg-paper border border-parchment-line rounded-md px-4 py-3 flex items-center justify-between text-sm"
              >
                <span>{doc.original_filename}</span>
                <span className="font-mono text-xs text-ink/50 uppercase">
                  {doc.document_type ?? doc.status}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>

      {summary ? (
        <>
          <section className="mb-10">
            <h2 className="font-display text-xl mb-3">Attorney briefing</h2>
            <p className="bg-paper border border-parchment-line rounded-md p-5 text-sm leading-relaxed">
              {summary.attorney_notes}
            </p>
          </section>

          <section className="mb-10">
            <h2 className="font-display text-xl mb-3">Timeline</h2>
            <p className="bg-paper border border-parchment-line rounded-md p-5 text-sm leading-relaxed">
              {summary.timeline_narrative}
            </p>
          </section>

          <section className="mb-10">
            <h2 className="font-display text-xl mb-3">Flags</h2>
            <FlagsList flags={summary.flags} />
          </section>

          <p className="text-xs text-ink/40 italic">{summary.disclaimer}</p>
        </>
      ) : (
        <p className="text-sm text-ink/50">
          The briefing will appear here once at least one document has finished processing.
        </p>
      )}
    </main>
  );
}
