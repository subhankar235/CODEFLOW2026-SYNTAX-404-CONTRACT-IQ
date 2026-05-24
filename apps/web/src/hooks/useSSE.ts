import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

const RECONNECT_DELAY_MS = 2000;

export type ClauseResult = {
  clause_id?: string;
  position_index: number;
  text: string;
  risk_level: string;
  triage: string;
  risk_categories: string[];
  plain_english: string;
  worst_case_scenario: string;
  financial_exposure?: string | null;
  negotiable?: boolean;
  confidence?: number;
  headline?: string | null;
  scenario?: string | null;
  probability?: string;
  similar_case?: string | null;
};

export function useSSE({
  token,
  baseUrl = "",
  maxRetries = 3,
  onClause,
  onProgress,
  onComplete,
  onError,
}: {
  token: string;
  baseUrl?: string;
  maxRetries?: number;
  onClause?: (result: ClauseResult) => void;
  onProgress?: (progress: number, step: string) => void;
  onComplete?: (summary: Record<string, unknown>) => void;
  onError?: (error: string) => void;
}) {
  const [status, setStatus] = useState<
    "idle" | "connecting" | "open" | "complete" | "error"
  >("idle");

  const esRef = useRef<EventSource | null>(null);
  const retriesRef = useRef(0);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const jobIdRef = useRef<string | null>(null);
  const tokenRef = useRef(token);

  const onClauseRef = useRef(onClause);
  const onProgressRef = useRef(onProgress);
  const onCompleteRef = useRef(onComplete);
  const onErrorRef = useRef(onError);

  useEffect(() => {
    onClauseRef.current = onClause;
    onProgressRef.current = onProgress;
    onCompleteRef.current = onComplete;
    onErrorRef.current = onError;
  }, [onClause, onProgress, onComplete, onError]);

  const closeEventSource = useCallback(() => {
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
    if (esRef.current) {
      esRef.current.close();
      esRef.current = null;
    }
  }, []);

  const dispose = useCallback(() => {
    closeEventSource();
    setStatus("idle");
    jobIdRef.current = null;
    retriesRef.current = 0;
  }, [closeEventSource]);

  useEffect(() => {
    return () => {
      dispose();
    };
  }, [dispose]);

  // ── Connect function stored in ref to allow self-reference ───────────
  const connectFnRef = useRef<(jobId: string) => void>(() => {});

  useEffect(() => {
    const createEventSource = (jobId: string) => {
      if (esRef.current && esRef.current.readyState !== EventSource.CLOSED) {
        return;
      }

      closeEventSource();
      setStatus("connecting");
      jobIdRef.current = jobId;
      retriesRef.current = 0;

      const url = `${baseUrl}/v1/scan/${jobId}/stream?token=${encodeURIComponent(tokenRef.current)}`;

      const es = new EventSource(url);
      esRef.current = es;

      es.onopen = () => {
        setStatus("open");
        retriesRef.current = 0;
      };

      es.onmessage = (event: MessageEvent<string>) => {
        try {
          const payload = JSON.parse(event.data);
          if (payload.type === "clause" && payload.data) {
            onClauseRef.current?.(payload.data);
          }
        } catch {
          console.warn("[useSSE] Failed to parse message:", event.data);
        }
      };

      es.addEventListener("progress", (event: MessageEvent<string>) => {
        try {
          const payload = JSON.parse(event.data);
          onProgressRef.current?.(payload.progress_pct ?? 0, payload.step ?? "");
        } catch {
          console.warn("[useSSE] Failed to parse progress:", event.data);
        }
      });

      es.addEventListener("complete", (event: MessageEvent<string>) => {
        try {
          const payload = JSON.parse(event.data);
          setStatus("complete");
          onCompleteRef.current?.(payload.summary ?? {});
        } catch {
          setStatus("complete");
          onCompleteRef.current?.({});
        }
        closeEventSource();
      });

      es.addEventListener("error", (event: Event) => {
        // Connection errors dispatch an Event with no data — ignore them;
        // onerror below handles reconnection. Only react to actual server-sent
        // `event: error` payloads.
        const msgEvent = event as MessageEvent<string>;
        if (!msgEvent.data) return;
        try {
          const payload = JSON.parse(msgEvent.data);
          setStatus("error");
          onErrorRef.current?.(payload.detail ?? "Stream error");
        } catch {
          // unparseable data — ignore, let onerror handle it
        }
      });

      es.onerror = () => {
        if (status !== "complete" && status !== "error") {
          if (retriesRef.current >= maxRetries) {
            setStatus("error");
            onErrorRef.current?.("Max reconnect attempts reached");
            return;
          }

          retriesRef.current += 1;
          const delay = RECONNECT_DELAY_MS * retriesRef.current;
          console.info(
            `[useSSE] Reconnecting (attempt ${retriesRef.current}/${maxRetries}) in ${delay}ms`,
          );
          setStatus("connecting");
          reconnectTimerRef.current = setTimeout(() => {
            const currentJobId = jobIdRef.current;
            if (currentJobId) {
              createEventSource(currentJobId);
            }
          }, delay);
        }
      };
    };

    connectFnRef.current = createEventSource;
  }, [token, baseUrl, closeEventSource, maxRetries, status]);

  const connect = useCallback(
    (jobId: string, token?: string) => {
      if (token) {
        tokenRef.current = token;
      }
      connectFnRef.current(jobId);
    },
    [],
  );

  return {
    status,
    connect,
    disconnect: dispose,
    error: status === "error" ? new Error("SSE error") : null,
  };
}