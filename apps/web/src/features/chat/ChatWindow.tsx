"use client";

import { useRef, useEffect } from "react";
import { useChat } from "@/hooks/useChat";
import { ChatMessage } from "./ChatMessage";
import { ChatInput } from "./ChatInput";

interface ChatWindowProps {
  contractId: string;
  jobId: string;
}

const STARTER_QUESTIONS = [
  "Can I work for a competitor after I leave?",
  "Who owns the code I write on weekends?",
  "What happens if I'm terminated?",
  "Are there any unusual intellectual property clauses?",
  "What are my notice period obligations?",
];

export function ChatWindow({ contractId, jobId }: ChatWindowProps) {
  const { messages, streamingText, isStreaming, sendMessage } = useChat({
    contractId,
    jobId,
  });
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom whenever messages or streaming text changes
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingText]);

  const handleStarterClick = (question: string) => {
    sendMessage(question);
  };

  const showEmptyState = messages.length === 0 && !isStreaming;

  return (
    <div className="flex h-full flex-col bg-[#0a0a0a]">
      {/* Conversation area */}
      <div className="flex-1 overflow-y-auto p-4 scroll-smooth">
        {showEmptyState ? (
          /* ── Starter questions ── */
          <div className="flex h-full flex-col items-center justify-center space-y-8 p-4">
            <div className="text-center space-y-3">
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-blue-500/10 mb-4">
                <span className="text-3xl">⚖️</span>
              </div>
              <h3 className="text-xl font-bold tracking-tight text-zinc-100">
                Contract Q&amp;A
              </h3>
              <p className="text-sm text-zinc-400 max-w-md">
                Ask specific questions about your contract. Our legal AI answers
                based on the full contract analysis.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-2xl">
              {STARTER_QUESTIONS.map((q) => (
                <button
                  key={q}
                  onClick={() => handleStarterClick(q)}
                  className="group rounded-xl border border-zinc-800 bg-zinc-900/50 p-4 text-sm font-medium text-left text-zinc-300 transition-all hover:border-blue-500/50 hover:bg-blue-500/5 hover:text-zinc-100 active:scale-[0.98]"
                >
                  <span className="mr-2 text-blue-400 group-hover:text-blue-300">
                    ›
                  </span>
                  {q}
                </button>
              ))}
            </div>
          </div>
        ) : (
          /* ── Chat history ── */
          <div className="mx-auto max-w-3xl space-y-2 pb-4">
            {messages.map((msg) => (
              <ChatMessage
                key={msg.id}
                message={msg}
                jobId={jobId}
                isStreaming={false}
              />
            ))}

            {/* Live streaming message */}
            {isStreaming && streamingText && (
              <ChatMessage
                key="streaming"
                message={{
                  id: "streaming",
                  role: "assistant",
                  content: streamingText,
                  clause_citation: null,
                  created_at: new Date().toISOString(),
                }}
                jobId={jobId}
                isStreaming={true}
              />
            )}

            {/* Typing indicator when streaming but no text yet */}
            {isStreaming && !streamingText && (
              <div className="flex items-center gap-3 px-4 py-2">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-500/10">
                  <span className="text-sm">⚖️</span>
                </div>
                <div className="flex gap-1.5">
                  {[0, 1, 2].map((i) => (
                    <div
                      key={i}
                      className="h-2 w-2 rounded-full bg-zinc-500 animate-bounce"
                      style={{ animationDelay: `${i * 150}ms` }}
                    />
                  ))}
                </div>
              </div>
            )}

            <div ref={bottomRef} />
          </div>
        )}
      </div>

      {/* Input area */}
      <div className="mx-auto w-full max-w-3xl">
        <ChatInput onSend={sendMessage} isStreaming={isStreaming} />
      </div>
    </div>
  );
}
