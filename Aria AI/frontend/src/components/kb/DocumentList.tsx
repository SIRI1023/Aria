import { FileText, Trash2, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";

type Doc = { id: string; filename: string };

export function DocumentList({
  documents,
  onDelete,
  loading,
}: {
  documents: Doc[];
  onDelete: (id: string) => void;
  loading: boolean;
}) {
  if (loading) {
    return (
      <div className="flex items-center gap-2 text-sm text-gray-400">
        <Loader2 className="h-4 w-4 animate-spin" />
        Loading documents...
      </div>
    );
  }

  if (documents.length === 0) {
    return <p className="text-sm text-gray-400">No documents uploaded yet.</p>;
  }

  return (
    <div className="space-y-2">
      {documents.map((doc) => (
        <div
          key={doc.id}
          className="flex items-center gap-3 bg-white border rounded-lg px-4 py-3"
        >
          <FileText className="h-4 w-4 text-violet-500 shrink-0" />
          <span className="text-sm text-gray-700 flex-1 truncate">{doc.filename}</span>
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7 text-gray-400 hover:text-red-500"
            onClick={() => onDelete(doc.id)}
          >
            <Trash2 className="h-3.5 w-3.5" />
          </Button>
        </div>
      ))}
    </div>
  );
}
