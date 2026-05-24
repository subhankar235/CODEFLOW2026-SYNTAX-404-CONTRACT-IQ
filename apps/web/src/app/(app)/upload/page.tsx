"use client";

import { useState, useCallback, useEffect } from "react";
import { useRouter } from "next/navigation";
import { FileText, Upload as UploadIcon, CheckCircle2, Loader2, Sparkles, ShieldCheck, AlertTriangle } from "lucide-react";
import { motion } from "framer-motion";
import { useUploadThing } from "@/lib/uploadthing";
import { useScanStore } from "@/store/scanStore";
import { useApiClient } from "@/lib/api";

type UploadPhase = "idle" | "uploading" | "processing" | "complete" | "error";

export default function UploadPage() {
  const router = useRouter();
  const api = useApiClient();
  const { startUpload } = useUploadThing("contractUploader");
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadPhase, setUploadPhase] = useState<UploadPhase>("idle");
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const handleFileUpload = useCallback(async (file: File) => {
    setSelectedFile(file);
    setUploadPhase("uploading");
    setUploadProgress(10);

    try {
      const uploadResult = await startUpload([file]);
      if (!uploadResult || uploadResult.length === 0) {
        throw new Error("Upload failed — no response from upload service");
      }

      setUploadProgress(50);

      const uploadedFile = uploadResult[0];

      const response = await api.upload(
        uploadedFile.ufsUrl,
        file.name,
        file.type || "application/octet-stream",
        file.size,
      );

      setUploadProgress(90);

      useScanStore.getState().setScanJob(response.job_id, response.contract_id);
      useScanStore.getState().updateProgress(0, "queued");
      router.push(`/scan/${response.job_id}`);
    } catch (err) {
      console.error("Upload error:", err);
      setError(err instanceof Error ? err.message : "Upload failed");
      setUploadPhase("error");
    }
  }, [router, startUpload, api]);

  const validateAndStartUpload = (file: File) => {
    const validTypes = ['pdf', 'docx'];
    const fileExtension = file.name.split('.').pop()?.toLowerCase();
    
    if (!fileExtension || !validTypes.includes(fileExtension)) {
      setError("Only PDF and DOCX files are accepted");
      return;
    }
    
    if (file.size > 25 * 1024 * 1024) {
      setError("File size must be less than 25MB");
      return;
    }
    
    setError(null);
    handleFileUpload(file);
  };

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndStartUpload(e.dataTransfer.files[0]);
    }
  }, []);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      validateAndStartUpload(e.target.files[0]);
    }
  }, []);

  const handleReset = () => {
    setSelectedFile(null);
    setUploadPhase("idle");
    setUploadProgress(0);
    setError(null);
  };

  const getPhaseLabel = () => {
    switch (uploadPhase) {
      case "uploading": return "Processing your document...";
      case "processing": return "Finalizing analysis...";
      default: return "Uploading...";
    }
  };

  const getProgressValue = () => {
    return uploadProgress;
  };

  return (
    <div className="max-w-4xl mx-auto py-12 px-4 sm:px-6 relative flex flex-col justify-center flex-1 min-h-[70vh]">
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-blue-600/10 rounded-full blur-[120px] pointer-events-none" />

      <div className="text-center mb-10 relative z-10">
        <h1 className="text-3xl font-bold text-white mb-3">New Analysis</h1>
        <p className="text-zinc-400">Upload your contract to securely analyze risks and generate safer counter-offers.</p>
      </div>

      <div className="relative z-10 w-full">
        {uploadPhase === "idle" && (
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className={`
              glass-panel relative rounded-3xl border-2 border-dashed transition-all duration-300 flex flex-col items-center justify-center p-16 cursor-pointer
              ${isDragging ? 'border-blue-500 bg-blue-500/5 shadow-[0_0_30px_rgba(59,130,246,0.2)]' : 'border-white/20 hover:border-white/40 hover:bg-white/5'}
            `}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => document.getElementById("file-upload")?.click()}
          >
            <input 
              id="file-upload" 
              type="file" 
              className="hidden" 
              accept=".pdf,.docx"
              onChange={handleFileSelect}
            />
            <div className="h-20 w-20 rounded-full bg-white/5 flex items-center justify-center mb-6 border border-white/10">
              <UploadIcon className="h-8 w-8 text-blue-400" />
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">Click or drag file to upload</h3>
            <p className="text-zinc-500 mb-6 text-sm">PDF or DOCX up to 25MB</p>
            <div className="flex items-center gap-2 text-xs text-zinc-400 bg-white/5 px-3 py-1.5 rounded-full border border-white/10">
               <ShieldCheck className="h-3 w-3 text-green-400" /> Encrypted before leaving device
            </div>
            {error && (
              <motion.div 
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="mt-4 flex items-center gap-2 text-red-400 text-sm bg-red-500/10 px-4 py-2 rounded-lg"
              >
                <AlertTriangle className="h-4 w-4" />
                {error}
              </motion.div>
            )}
          </motion.div>
        )}

        {(uploadPhase === "uploading" || uploadPhase === "processing") && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="glass-panel p-8 rounded-3xl border border-white/10 max-w-xl mx-auto"
          >
            <div className="flex items-center justify-between mb-8">
              <div className="flex items-center gap-3">
                <FileText className="h-8 w-8 text-blue-400" />
                <div>
                  <h3 className="text-white font-medium">{selectedFile?.name}</h3>
                  <p className="text-zinc-500 text-sm">{(selectedFile?.size ? (selectedFile.size / 1024 / 1024).toFixed(2) : "0.00")} MB</p>
                </div>
              </div>
              {uploadPhase !== "processing" && <Sparkles className="h-6 w-6 text-blue-400 animate-pulse" />}
            </div>

            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <Loader2 className="h-5 w-5 text-blue-400 animate-spin" />
                <span className="text-zinc-300">{getPhaseLabel()}</span>
              </div>

              <div className="w-full bg-zinc-800 rounded-full h-2 overflow-hidden">
                <motion.div 
                  className="h-full bg-blue-500 rounded-full"
                  initial={{ width: 0 }}
                  animate={{ width: `${getProgressValue()}%` }}
                  transition={{ duration: 0.3 }}
                />
              </div>

              <div className="flex items-center justify-between text-xs text-zinc-500 mt-4">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="h-3 w-3 text-green-400" />
                  Processing your document
                </div>
                <span>{Math.round(getProgressValue())}%</span>
              </div>
            </div>
          </motion.div>
        )}

        {uploadPhase === "error" && (
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="glass-panel p-10 rounded-3xl border border-red-500/30 bg-red-500/5 max-w-md mx-auto text-center"
          >
            <div className="w-20 h-20 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
              <AlertTriangle className="h-10 w-10 text-red-400" />
            </div>
            <h2 className="text-2xl font-bold text-white mb-2">Upload Failed</h2>
            <p className="text-zinc-400 mb-8">
              {error || "Something went wrong. Please try again."}
            </p>
            <button
              onClick={handleReset}
              className="w-full py-4 bg-white text-black font-bold rounded-xl hover:bg-zinc-200 transition-all"
            >
              Try Again
            </button>
          </motion.div>
        )}
      </div>
    </div>
  );
}