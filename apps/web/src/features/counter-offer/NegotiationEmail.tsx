"use client";

import { useState } from "react";
import { Copy, CheckCircle2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface NegotiationEmailProps {
  emailBody: string;
}

export function NegotiationEmail({ emailBody }: NegotiationEmailProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(emailBody);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-foreground">Suggested Email to Counterparty</h3>
        <button
          onClick={handleCopy}
          className={cn(
            "flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-all",
            copied
              ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
              : "bg-primary text-primary-foreground hover:bg-primary/90"
          )}
        >
          {copied ? (
            <>
              <CheckCircle2 className="h-4 w-4" />
              Copied!
            </>
          ) : (
            <>
              <Copy className="h-4 w-4" />
              Copy Email
            </>
          )}
        </button>
      </div>
      <div className="rounded-md border bg-muted/40 p-4 font-mono text-sm leading-relaxed text-muted-foreground whitespace-pre-wrap">
        {emailBody}
      </div>
    </div>
  );
}
