"use client";

import { useState, useRef, useEffect } from "react";
import { MessageBubble } from "@/components/chat/MessageBubble";
import { ChatInput } from "@/components/chat/ChatInput";
import { AgentTrace } from "@/components/agent/AgentTrace";
import { streamAgent, type Message, type AgentStep } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Bot, BookOpen } from "lucide-react";
import Link from "next/link";

type MessageWithTrace = Message & { steps?: AgentStep[] };

export default function Home() {
  const [messages, setMessages] = useState<MessageWithTrace[]>([]);
  const [streaming, setStreaming] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async (text: string) => {
    const userMessage: MessageWithTrace = { role: "user", content: text };
    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);
    setStreaming(true);

    const assistantMsg: MessageWithTrace = { role: "assistant", content: "", steps: [] };
    setMessages([...updatedMessages, assistantMsg]);

    await streamAgent(
      updatedMessages,
      (step: AgentStep) => {
        setMessages((prev) => {
          const next = [...prev];
          const last = { ...next[next.length - 1] };
          if (step.type === "final_answer") {
            last.content = step.content;
          } else {
            last.steps = [...(last.steps || []), step];
          }
          next[next.length - 1] = last;
          return next;
        });
      },
      () => setStreaming(false)
    );
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      <header className="bg-white border-b px-6 py-4 flex items-center gap-3 shrink-0">
        <div className="h-9 w-9 rounded-xl bg-violet-600 flex items-center justify-center">
          <Bot className="h-5 w-5 text-white" />
        </div>
        <div>
          <h1 className="font-semibold text-gray-900">Aria</h1>
          <p className="text-xs text-gray-500">AI Business Operations Assistant</p>
        </div>
        <div className="ml-auto flex items-center gap-3">
          <Link
            href="/kb"
            className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-violet-600 transition-colors"
          >
            <BookOpen className="h-4 w-4" />
            Knowledge Base
          </Link>
          <Badge variant="outline" className="text-xs text-green-600 border-green-300">
            ● Online
          </Badge>
        </div>
      </header>

      <Separator />

      <div className="flex-1 overflow-y-auto px-4 py-6 max-w-3xl mx-auto w-full">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center gap-3">
            <div className="h-16 w-16 rounded-2xl bg-violet-100 flex items-center justify-center">
              <Bot className="h-8 w-8 text-violet-600" />
            </div>
            <h2 className="text-xl font-semibold text-gray-800">How can I help you today?</h2>
            <p className="text-sm text-gray-500 max-w-sm">
              Ask me anything, or upload documents to the{" "}
              <Link href="/kb" className="text-violet-600 hover:underline">Knowledge Base</Link>{" "}
              to get cited answers.
            </p>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i}>
            {msg.role === "assistant" && msg.steps && msg.steps.length > 0 && (
              <AgentTrace steps={msg.steps} />
            )}
            {(msg.content || msg.role === "user") && (
              <MessageBubble message={msg} />
            )}
          </div>
        ))}

        {streaming && messages[messages.length - 1]?.content === "" &&
          (messages[messages.length - 1]?.steps?.length ?? 0) === 0 && (
          <div className="flex gap-3 mb-4">
            <div className="h-8 w-8 rounded-full bg-violet-100 flex items-center justify-center shrink-0">
              <Bot className="h-4 w-4 text-violet-600" />
            </div>
            <div className="bg-gray-100 rounded-2xl rounded-tl-sm px-4 py-2.5 flex gap-1 items-center">
              <span className="h-2 w-2 rounded-full bg-violet-400 animate-bounce [animation-delay:0ms]" />
              <span className="h-2 w-2 rounded-full bg-violet-400 animate-bounce [animation-delay:150ms]" />
              <span className="h-2 w-2 rounded-full bg-violet-400 animate-bounce [animation-delay:300ms]" />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="shrink-0 px-4 pb-6 max-w-3xl mx-auto w-full">
        <ChatInput onSend={handleSend} disabled={streaming} />
        <p className="text-xs text-center text-gray-400 mt-2">
          Aria · Powered by Claude + LangGraph · Phase 3
        </p>
      </div>
    </div>
  );
}
