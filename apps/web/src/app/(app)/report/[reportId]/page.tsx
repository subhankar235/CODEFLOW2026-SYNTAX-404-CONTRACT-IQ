"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { useApiClient } from "@/lib/api";
import { Report } from "@/types/api";
import { Loader2, ArrowLeft } from "lucide-react";
import { ShareButton } from "@/features/report/ShareButton";
import { DownloadButton } from "@/features/report/DownloadButton";
import Link from "next/link";

export default function ReportPage() {
  const params = useParams();
  const reportId = params?.reportId as string;
  const { getReport } = useApiClient();
  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await getReport(reportId);
        setReport(data);
      } catch (err) {
        console.error("Failed to load report", err);
      } finally {
        setLoading(false);
      }
    }
    if (reportId) load();
  }, [reportId, getReport]);

  if (loading) {
    return (
      <div className="flex h-[calc(100vh-4rem)] items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-sm text-muted-foreground">Loading report...</p>
        </div>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="flex h-[calc(100vh-4rem)] flex-col items-center justify-center gap-4">
        <p className="text-muted-foreground">Report not found or has expired.</p>
        <Link href="/dashboard" className="text-sm font-medium text-primary hover:underline">
          Return to Dashboard
        </Link>
      </div>
    );
  }

  const shareUrl = typeof window !== "undefined" 
    ? `${window.location.origin}/share/${report.share_uuid}`
    : "";

  return (
    <div className="container mx-auto max-w-5xl py-8">
      <div className="mb-8 flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Link href="/dashboard" className="text-muted-foreground hover:text-foreground transition-colors">
              <ArrowLeft className="h-4 w-4" />
            </Link>
            <h1 className="text-2xl font-bold tracking-tight">Contract Analysis Report</h1>
          </div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground pl-6">
            <span>Generated on {new Date(report.created_at).toLocaleDateString()}</span>
            <span>•</span>
            <span className="uppercase">{report.language} Version</span>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          <ShareButton shareUrl={shareUrl} />
          <DownloadButton pdfUrl={report.pdf_path} filename={`Report-${report.id}.pdf`} />
        </div>
      </div>

      <div className="relative aspect-[1/1.414] w-full overflow-hidden rounded-xl border bg-card shadow-lg">
        <iframe
          src={`${report.pdf_path}#view=FitH`}
          className="h-full w-full border-0"
          title="PDF Report Viewer"
        />
        
        <div className="absolute inset-x-0 bottom-0 flex justify-center bg-gradient-to-t from-black/20 to-transparent p-4">
           <p className="text-[10px] text-white/40 uppercase tracking-widest">LegalTech AI Generated Integrity Report</p>
        </div>
      </div>
    </div>
  );
}