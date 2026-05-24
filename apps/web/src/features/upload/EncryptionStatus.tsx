"use client";

import { Lock, AlertTriangle } from "lucide-react";

interface EncryptionStatusProps {
  keyHash?: string;
  onClear?: () => void;
}

export function EncryptionStatus({ keyHash, onClear }: EncryptionStatusProps) {
  return (
    <div className="p-4 border border-zinc-200 bg-zinc-50 rounded-lg">
      <div className="flex items-center gap-2 text-sm text-zinc-600 mb-2">
        <Lock className="h-4 w-4" />
        <span>End-to-end encrypted session</span>
      </div>
      {keyHash && (
        <p className="text-xs text-zinc-400 font-mono mb-2">
          Session key: {keyHash.slice(0, 16)}...
        </p>
      )}
      {onClear && (
        <button
          onClick={onClear}
          className="flex items-center gap-1 text-xs text-red-600 hover:text-red-700"
        >
          <AlertTriangle className="h-3 w-3" />
          Delete session data
        </button>
      )}
    </div>
  );
}