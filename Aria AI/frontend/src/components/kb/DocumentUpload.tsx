"use client";

import { useState, useRef } from "react";
import { uploadDocument } from "@/lib/api";
import { Upload, Loader2, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";

export function DocumentUpload({ onSuccess }: { onSuccess: () => void }) {
  const [uploading, setUploading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = async (file: File) => {
    setUploading(true);
    setError("");
    setSuccess(false);
    try {
      await uploadDocument(file);
      setSuccess(true);
      onSuccess();
      setTimeout(() => setSuccess(false), 3000);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Upload failed. Please try again.");
    } finally {
      setUploading(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  };

  return (
    <div
      onDrop={(e) => { e.preventDefault(); const f = e.dataTransfer.files[0]; if (f) handleFile(f); }}
      onDragOver={(e) => e.preventDefault()}
      className="border-2 border-dashed border-gray-200 rounded-xl p-8 text-center hover:border-violet-300 transition-colors"
    >
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.txt,.md"
        className="hidden"
        onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f); }}
      />

      {uploading ? (
        <div className="flex flex-col items-center gap-2">
          <Loader2 className="h-8 w-8 text-violet-500 animate-spin" />
          <p className="text-sm text-gray-500">Processing document...</p>
        </div>
      ) : success ? (
        <div className="flex flex-col items-center gap-2">
          <CheckCircle2 className="h-8 w-8 text-green-500" />
          <p className="text-sm text-green-600">Document uploaded successfully!</p>
        </div>
      ) : (
        <div className="flex flex-col items-center gap-3">
          <Upload className="h-8 w-8 text-gray-400" />
          <div>
            <p className="text-sm font-medium text-gray-700">Drop a file here or</p>
            <Button
              variant="link"
              className="text-violet-600 p-0 h-auto text-sm"
              onClick={() => inputRef.current?.click()}
            >
              browse to upload
            </Button>
          </div>
          <p className="text-xs text-gray-400">PDF, TXT, or Markdown</p>
        </div>
      )}

      {error && <p className="mt-3 text-sm text-red-500">{error}</p>}
    </div>
  );
}
