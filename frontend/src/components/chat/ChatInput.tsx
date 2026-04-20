"use client";

import { useRef, KeyboardEvent } from "react";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { SendHorizonal } from "lucide-react";

type Props = {
  onSend: (text: string) => void;
  disabled?: boolean;
};

export function ChatInput({ onSend, disabled }: Props) {
  const ref = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    const text = ref.current?.value.trim();
    if (!text || disabled) return;
    onSend(text);
    ref.current!.value = "";
    ref.current!.style.height = "auto";
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex gap-2 items-end border rounded-2xl p-2 bg-white shadow-sm">
      <Textarea
        ref={ref}
        placeholder="Ask Aria anything... (Shift+Enter for new line)"
        className="resize-none border-0 shadow-none focus-visible:ring-0 min-h-[40px] max-h-32 text-sm"
        rows={1}
        disabled={disabled}
        onKeyDown={handleKeyDown}
        onChange={(e) => {
          e.target.style.height = "auto";
          e.target.style.height = e.target.scrollHeight + "px";
        }}
      />
      <Button
        size="icon"
        onClick={handleSend}
        disabled={disabled}
        className="shrink-0 rounded-xl bg-violet-600 hover:bg-violet-700"
      >
        <SendHorizonal className="h-4 w-4" />
      </Button>
    </div>
  );
}
