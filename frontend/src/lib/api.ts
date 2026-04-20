const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type Message = {
  role: "user" | "assistant";
  content: string;
};

export async function streamChat(
  messages: Message[],
  onChunk: (text: string) => void,
  onDone: () => void
) {
  const response = await fetch(`${API_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages }),
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
      } catch {}
    }
  }
  onDone();
}
