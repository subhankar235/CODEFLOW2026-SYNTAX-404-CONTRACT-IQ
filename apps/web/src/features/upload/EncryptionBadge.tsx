"use client";

import { Lock, CheckCircle } from "lucide-react";

interface EncryptionBadgeProps {
  status: "idle" | "encrypting" | "complete";
}

export function EncryptionBadge({ status }: EncryptionBadgeProps) {
  if (status === "idle") return null;

  return (
    <div className="flex items-center gap-2 p-3 bg-green-50 rounded-lg animate-pulse">
      {status === "encrypting" ? (
        <>
          <Lock className="h-5 w-5 text-green-600" />
          <span className="text-sm text-green-700">
            Encrypting your document...
          </span>
        </>
      ) : (
        <>
          <CheckCircle className="h-5 w-5 text-green-600" />
          <span className="text-sm text-green-700">
            Document encrypted before leaving your device
          </span>
        </>
      )}
    </div>
  );
}