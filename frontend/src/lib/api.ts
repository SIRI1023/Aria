const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type Citation = {
  filename: string;
  page: number;
};

export type Message = {
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
};

export async function streamChat(
  messages: Message[],
  onChunk: (text: string) => void,
  onDone: () => void,
  onCitations?: (citations: Citation[]) => void
) {
  const response = await fetch(`${API_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages: messages.map(({ role, content }) => ({ role, content })) }),
  });

  if (!response.body) throw new Error("No response body");

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const lines = decoder.decode(value).split("\n");
    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      const data = line.slice(6);
      if (data === "[DONE]") { onDone(); return; }
      try {
        const parsed = JSON.parse(data);
        if (parsed.text) onChunk(parsed.text);
        if (parsed.citations && onCitations) onCitations(parsed.citations);
      } catch {}
    }
  }
  onDone();
}

export type AgentStep =
  | { type: "tool_call"; tool: string; args: Record<string, string> }
  | { type: "tool_result"; tool: string; content: string }
  | { type: "final_answer"; content: string };

export async function streamAgent(
  messages: Message[],
  onStep: (step: AgentStep) => void,
  onDone: () => void
) {
  const response = await fetch(`${API_URL}/api/agent`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages: messages.map(({ role, content }) => ({ role, content })) }),
  });

  if (!response.body) throw new Error("No response body");

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    const lines = decoder.decode(value).split("\n");
    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      const data = line.slice(6);
      if (data === "[DONE]") { onDone(); return; }
      try {
        const parsed = JSON.parse(data);
        onStep(parsed as AgentStep);
      } catch {}
    }
  }
  onDone();
}

export async function uploadDocument(file: File): Promise<{ id: string; filename: string; chunks: number }> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch(`${API_URL}/api/documents/upload`, {
    method: "POST",
    body: formData,
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || "Upload failed");
  }
  return response.json();
}

export async function listDocuments(): Promise<{ id: string; filename: string }[]> {
  const response = await fetch(`${API_URL}/api/documents`);
  if (!response.ok) throw new Error("Failed to fetch documents");
  return response.json();
}

export async function deleteDocument(id: string): Promise<void> {
  await fetch(`${API_URL}/api/documents/${id}`, { method: "DELETE" });
}
