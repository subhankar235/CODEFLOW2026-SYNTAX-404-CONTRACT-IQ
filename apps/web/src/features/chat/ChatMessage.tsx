import { cn } from "@/lib/utils";
import { Bot, User } from "lucide-react";
import { ChatMessage as IChatMessage } from "@/types/api";
import { ClauseCitation } from "./ClauseCitation";

interface ChatMessageProps {
  message: IChatMessage;
  jobId: string;
  isStreaming?: boolean;
}

export function ChatMessage({ message, jobId, isStreaming = false }: ChatMessageProps) {
  const isUser = message.role === "user";

  return (
    <div
      className={cn(
        "flex w-full gap-3 px-2 py-1",
        isUser ? "justify-end" : "justify-start"
      )}
    >
      {/* AI avatar */}
      {!isUser && (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-500/10 mt-1">
          <Bot className="h-4 w-4 text-blue-400" />
        </div>
      )}

      <div className={cn("flex max-w-[80%] flex-col gap-1.5", isUser && "items-end")}>
        {/* Bubble */}
        <div
          className={cn(
            "rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap break-words",
            isUser
              ? "bg-blue-600 text-white rounded-tr-sm"
              : "bg-zinc-800/80 text-zinc-100 rounded-tl-sm border border-zinc-700/50"
          )}
        >
          {message.content}
          {/* Streaming cursor */}
          {isStreaming && (
            <span className="ml-0.5 inline-block h-4 w-0.5 bg-blue-400 animate-pulse align-middle" />
          )}
        </div>

        {/* Clause citation pill (AI messages only, after streaming completes) */}
        {message.clause_citation && !isUser && !isStreaming && (
          <ClauseCitation
            clauseId={message.clause_citation}
            jobId={jobId}
            label="View Referenced Clause"
          />
        )}
      </div>

      {/* User avatar */}
      {isUser && (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-zinc-700 mt-1">
          <User className="h-4 w-4 text-zinc-300" />
        </div>
      )}
    </div>
  );
}
