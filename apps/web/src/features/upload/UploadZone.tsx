"use client";

import { useState, useCallback } from "react";
import { Upload, FileText, X, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";

interface UploadZoneProps {
  onFileSelect: (file: File) => void;
  disabled?: boolean;
  accept?: string;
}

export function UploadZone({
  onFileSelect,
  disabled = false,
  accept = ".pdf,.docx",
}: UploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);

  const maxSize = 25 * 1024 * 1024; // 25MB

  const validateFile = useCallback(
    (file: File): string | null => {
      const ext = file.name.split(".").pop()?.toLowerCase();
      if (!["pdf", "docx"].includes(ext || "")) {
        return "Only PDF and DOCX files are accepted";
      }
      if (file.size > maxSize) {
        return "File must be under 25MB";
      }
      return null;
    },
    [maxSize]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);

      if (disabled) return;

      const file = e.dataTransfer.files[0];
      if (!file) return;

      const err = validateFile(file);
      if (err) {
        setError(err);
        return;
      }

      setError(null);
      setSelectedFile(file);
      onFileSelect(file);
    },
    [disabled, onFileSelect, validateFile]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (!file) return;

      const err = validateFile(file);
      if (err) {
        setError(err);
        return;
      }

      setError(null);
      setSelectedFile(file);
      onFileSelect(file);
    },
    [onFileSelect, validateFile]
  );

  const clearFile = useCallback(() => {
    setSelectedFile(null);
    setError(null);
  }, []);

  if (selectedFile) {
    return (
      <div className="p-6 border-2 border-green-300 bg-green-50 rounded-lg">
        <div className="flex items-center gap-3">
          <FileText className="h-8 w-8 text-green-600" />
          <div className="flex-1 min-w-0">
            <p className="font-medium text-zinc-900 truncate">
              {selectedFile.name}
            </p>
            <p className="text-sm text-zinc-500">
              {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
            </p>
          </div>
          <button
            onClick={clearFile}
            className="p-1 hover:bg-green-100 rounded"
            disabled={disabled}
          >
            <X className="h-5 w-5 text-green-600" />
          </button>
        </div>
      </div>
    );
  }

  return (
    <div>
      <label
        className={cn(
          "flex flex-col items-center justify-center w-full h-48 border-2 border-dashed rounded-lg cursor-pointer transition-colors",
          isDragging
            ? "border-zinc-900 bg-zinc-50"
            : "border-zinc-300 hover:border-zinc-400 hover:bg-zinc-50",
          disabled && "opacity-50 cursor-not-allowed"
        )}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
      >
        <input
          type="file"
          className="hidden"
          accept={accept}
          onChange={handleFileInput}
          disabled={disabled}
        />
        <Upload className="h-10 w-10 text-zinc-400 mb-3" />
        <p className="text-sm font-medium text-zinc-600">
          Drop your contract here or click to browse
        </p>
        <p className="text-xs text-zinc-400 mt-1">
          PDF or DOCX • Max 25MB
        </p>
      </label>
      {error && (
        <div className="flex items-center gap-2 mt-2 text-sm text-red-600">
          <AlertCircle className="h-4 w-4" />
          {error}
        </div>
      )}
    </div>
  );
}