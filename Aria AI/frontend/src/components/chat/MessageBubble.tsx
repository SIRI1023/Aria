"use client";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";
import type { Message } from "@/lib/api";

export function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";

  return (
    <div className={cn("flex gap-3 mb-4", isUser && "flex-row-reverse")}>
      <Avatar className="h-8 w-8 shrink-0">
        <AvatarFallback className={cn(
          "text-xs font-medium",
          isUser ? "bg-blue-600 text-white" : "bg-violet-600 text-white"
        )}>
          {isUser ? "You" : "AI"}
        </AvatarFallback>
      </Avatar>
      <div className="flex flex-col gap-1.5 max-w-[75%]">
        <div className={cn(
          "rounded-2xl px-4 py-2.5 text-sm leading-relaxed whitespace-pre-wrap",
          isUser
            ? "bg-blue-600 text-white rounded-tr-sm"
            : "bg-gray-100 text-gray-900 rounded-tl-sm"
        )}>
          {message.content}
        </div>
        {message.citations && message.citations.length > 0 && (
          <div className="flex flex-wrap gap-1.5 px-1">
            {message.citations.map((c, i) => (
              <span
                key={i}
                className="inline-flex items-center gap-1 text-xs bg-violet-50 text-violet-700 border border-violet-200 rounded-full px-2 py-0.5"
              >
                <span className="font-medium">Source {i + 1}:</span>
                {c.filename}{c.page > 0 ? `, p.${c.page}` : ""}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
