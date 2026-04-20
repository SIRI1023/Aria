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
      <div className={cn(
        "max-w-[75%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed whitespace-pre-wrap",
        isUser
          ? "bg-blue-600 text-white rounded-tr-sm"
          : "bg-gray-100 text-gray-900 rounded-tl-sm"
      )}>
        {message.content}
      </div>
    </div>
  );
}
