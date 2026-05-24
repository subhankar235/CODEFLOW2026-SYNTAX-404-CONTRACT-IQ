export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  clause_citation: string | null;
  created_at: string;
}

export interface ChatRequest {
  message: string;
  conversation_id?: string;
}