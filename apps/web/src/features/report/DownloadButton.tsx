"use client";

import { Download } from "lucide-react";

interface DownloadButtonProps {
  pdfUrl: string;
  filename: string;
}

export function DownloadButton({ pdfUrl, filename }: DownloadButtonProps) {
  return (
    <a
      href={pdfUrl}
      download={filename}
      target="_blank"
      rel="noopener noreferrer"
      className="flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow-sm transition-colors hover:bg-primary/90"
    >
      <Download className="h-4 w-4" />
      Download PDF
    </a>
  );
}
