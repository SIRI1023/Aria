"use client";

import { useState, useEffect } from "react";
import { DocumentUpload } from "@/components/kb/DocumentUpload";
import { DocumentList } from "@/components/kb/DocumentList";
import { listDocuments, deleteDocument } from "@/lib/api";
import { Bot, MessageSquare } from "lucide-react";
import { Separator } from "@/components/ui/separator";
import Link from "next/link";

type Doc = { id: string; filename: string };

export default function KnowledgeBase() {
  const [documents, setDocuments] = useState<Doc[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchDocs = async () => {
    try {
      const docs = await listDocuments();
      setDocuments(docs);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchDocs(); }, []);

  const handleDelete = async (id: string) => {
    await deleteDocument(id);
    setDocuments((prev) => prev.filter((d) => d.id !== id));
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      <header className="bg-white border-b px-6 py-4 flex items-center gap-3 shrink-0">
        <div className="h-9 w-9 rounded-xl bg-violet-600 flex items-center justify-center">
          <Bot className="h-5 w-5 text-white" />
        </div>
        <div>
          <h1 className="font-semibold text-gray-900">Aria</h1>
          <p className="text-xs text-gray-500">Knowledge Base</p>
        </div>
        <div className="ml-auto">
          <Link
            href="/"
            className="flex items-center gap-1.5 text-sm text-violet-600 hover:text-violet-700"
          >
            <MessageSquare className="h-4 w-4" />
            Back to Chat
          </Link>
        </div>
      </header>

      <Separator />

      <div className="flex-1 overflow-y-auto p-6 max-w-3xl mx-auto w-full">
        <h2 className="text-lg font-semibold text-gray-900 mb-1">Upload Documents</h2>
        <p className="text-sm text-gray-500 mb-6">
          Upload PDFs, text files, or markdown. Aria will use them to answer your questions with citations.
        </p>

        <DocumentUpload onSuccess={fetchDocs} />

        <div className="mt-8">
          <h3 className="text-sm font-medium text-gray-700 mb-3">
            Uploaded Documents {!loading && `(${documents.length})`}
          </h3>
          <DocumentList documents={documents} onDelete={handleDelete} loading={loading} />
        </div>
      </div>
    </div>
  );
}
