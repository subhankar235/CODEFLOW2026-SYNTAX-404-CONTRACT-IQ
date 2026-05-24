"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { useApiClient } from "@/lib/api";
import { Report } from "@/types/api";
import { Loader2, ShieldCheck } from "lucide-react";
import { DownloadButton } from "@/features/report/DownloadButton";

export default function SharedReportPage() {
  const params = useParams();
  const shareUuid = params?.shareUuid as string;
  const { getSharedReport } = useApiClient();
  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await getSharedReport(shareUuid);
        setReport(data);
      } catch (err) {
        console.error("Failed to load shared report", err);
      } finally {
        setLoading(false);
      }
    }
    if (shareUuid) load();
  }, [shareUuid, getSharedReport]);

  if (loading) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-zinc-950">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
          <p className="text-sm text-zinc-400">Verifying secure link...</p>
        </div>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="flex h-screen w-full flex-col items-center justify-center gap-4 bg-zinc-950 px-4 text-center">
        <div className="h-16 w-16 rounded-full bg-red-500/10 flex items-center justify-center mb-2">
          <ShieldCheck className="h-8 w-8 text-red-500" />
        </div>
        <h1 className="text-xl font-bold text-white">Link Expired or Invalid</h1>
        <p className="text-sm text-zinc-400 max-w-xs">
          This shared report link may have expired or is no longer available. Please contact the sender for a new link.
        </p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-white selection:bg-blue-500/30">
      <header className="sticky top-0 z-10 border-b border-white/5 bg-zinc-950/80 backdrop-blur-md">
        <div className="container mx-auto flex h-16 max-w-5xl items-center justify-between px-4">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600">
              <ShieldCheck className="h-5 w-5 text-white" />
            </div>
            <span className="font-bold tracking-tight">LegalTech AI</span>
          </div>
          <DownloadButton pdfUrl={report.pdf_path} filename={`Shared-Report.pdf`} />
        </div>
      </header>

      <main className="container mx-auto max-w-5xl px-4 py-8">
        <div className="mb-8 space-y-2">
          <h1 className="text-3xl font-bold tracking-tight">Shared Contract Analysis</h1>
          <div className="flex items-center gap-2 text-sm text-zinc-400">
            <span>Secure Preview</span>
            <span>•</span>
            <span>Generated on {new Date(report.created_at).toLocaleDateString()}</span>
          </div>
        </div>

        <div className="relative aspect-[1/1.414] w-full overflow-hidden rounded-2xl border border-white/10 bg-zinc-900 shadow-2xl">
          <iframe
            src={`${report.pdf_path}#view=FitH`}
            className="h-full w-full border-0"
            title="PDF Report Viewer"
          />
        </div>
        
        <footer className="mt-12 border-t border-white/5 py-8 text-center text-zinc-500">
          <p className="text-xs uppercase tracking-widest">
            Protected by LegalTech AI End-to-End Encryption
          </p>
        </footer>
      </main>
    </div>
  );
}
