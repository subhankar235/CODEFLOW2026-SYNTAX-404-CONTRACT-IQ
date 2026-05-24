"use client";

import { cn } from "@/lib/utils";

interface UploadProgressProps {
  progress: number;
  phase: "encrypting" | "uploading" | "complete";
  fileName?: string;
}

export function UploadProgress({
  progress,
  phase,
  fileName,
}: UploadProgressProps) {
  const getPhaseLabel = () => {
    switch (phase) {
      case "encrypting":
        return "Encrypting...";
      case "uploading":
        return "Uploading...";
      case "complete":
        return "Complete!";
    }
  };

  return (
    <div className="w-full">
      <div className="flex items-center justify-between text-sm text-zinc-600 mb-2">
        <span className="truncate">{fileName}</span>
        <span>{getPhaseLabel()}</span>
      </div>
      <div className="h-2 w-full bg-zinc-200 rounded-full overflow-hidden">
        <div
          className={cn(
            "h-full bg-zinc-900 rounded-full transition-all duration-300",
            phase === "complete" && "bg-green-600"
          )}
          style={{ width: `${progress}%` }}
        />
      </div>
      <div className="flex justify-between text-xs text-zinc-400 mt-1">
        <span>0%</span>
        <span>{Math.round(progress)}%</span>
      </div>
    </div>
  );
}