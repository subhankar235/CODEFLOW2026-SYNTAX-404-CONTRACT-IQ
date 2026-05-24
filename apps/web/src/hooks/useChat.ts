"use client";

import { useState, useCallback, useRef } from "react";
import { useAuth } from "@clerk/nextjs";
import { ChatMessage } from "@/types/api";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface UseChatOptions {
  contractId: string;
  jobId?: string;
}

interface UseChatReturn {
  messages: ChatMessage[];
  streamingText: string;
  isStreaming: boolean;
  sendMessage: (text: string) => Promise<void>;
  clearMessages: () => void;
}

export function useChat({ contractId, jobId }: UseChatOptions): UseChatReturn {
  const { getToken } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [streamingText, setStreamingText] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);
  // Keep a stable ref to messages for building conversation history
  const messagesRef = useRef<ChatMessage[]>([]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    messagesRef.current = [];
    setStreamingText("");
  }, []);

  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim() || isStreaming) return;

      // Cancel any in-flight request
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      abortControllerRef.current = new AbortController();

      // Append user message immediately
      const userMsg: ChatMessage = {
        id: `user-${Date.now()}`,
        role: "user",
        content: text.trim(),
        clause_citation: null,
        created_at: new Date().toISOString(),
      };

      const updatedMessages = [...messagesRef.current, userMsg];
      setMessages(updatedMessages);
      messagesRef.current = updatedMessages;

      setIsStreaming(true);
      setStreamingText("");

      // Build conversation history for context (exclude last user message — sent as question)
      const conversationHistory = messagesRef.current
        .slice(0, -1) // exclude just-added user message
        .map((m) => ({ role: m.role, content: m.content }));

      try {
        const token = await getToken();
        const response = await fetch(
          `${API_URL}/api/v1/chat/${contractId}`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify({
              question: text.trim(),
              conversation_history: conversationHistory,
            }),
            signal: abortControllerRef.current.signal,
          }
        );

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${await response.text()}`);
        }

        // Read the streaming SSE response
        const reader = response.body?.getReader();
        if (!reader) throw new Error("No response body");

        const decoder = new TextDecoder();
        let accumulatedText = "";
        let clauseCitation: string | null = null;
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() ?? ""; // keep incomplete line in buffer

          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            const jsonStr = line.slice(6).trim();
            if (!jsonStr || jsonStr === "[DONE]") continue;

            try {
              const parsed = JSON.parse(jsonStr);

              if (parsed.type === "token" && parsed.content) {
                accumulatedText += parsed.content;
                setStreamingText(accumulatedText);
              } else if (parsed.type === "citation" && parsed.clause_id) {
                clauseCitation = parsed.clause_id;
              } else if (parsed.type === "error") {
                accumulatedText = parsed.content || "Sorry, I encountered an error.";
                setStreamingText(accumulatedText);
              }
            } catch {
              // If not JSON, treat as plain text token (for simple streaming backends)
              if (jsonStr && jsonStr !== "[DONE]") {
                accumulatedText += jsonStr;
                setStreamingText(accumulatedText);
              }
            }
          }
        }

        // Finalize: push the completed AI message
        const aiMsg: ChatMessage = {
          id: `ai-${Date.now()}`,
          role: "assistant",
          content: accumulatedText || "I could not generate a response.",
          clause_citation: clauseCitation,
          created_at: new Date().toISOString(),
        };

        const finalMessages = [...messagesRef.current, aiMsg];
        setMessages(finalMessages);
        messagesRef.current = finalMessages;
        setStreamingText("");
      } catch (err: unknown) {
        if (err instanceof Error && err.name === "AbortError") return;

        console.error("Chat error:", err);
        const errorMsg: ChatMessage = {
          id: `err-${Date.now()}`,
          role: "assistant",
          content:
            "Sorry, I encountered an error while processing your request. Please try again.",
          clause_citation: null,
          created_at: new Date().toISOString(),
        };
        const finalMessages = [...messagesRef.current, errorMsg];
        setMessages(finalMessages);
        messagesRef.current = finalMessages;
        setStreamingText("");
      } finally {
        setIsStreaming(false);
      }
    },
    [contractId, getToken, isStreaming]
  );

  return {
    messages,
    streamingText,
    isStreaming,
    sendMessage,
    clearMessages,
  };
}
