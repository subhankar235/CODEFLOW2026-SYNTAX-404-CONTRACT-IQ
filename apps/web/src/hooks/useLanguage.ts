"use client";

import { useCallback, useEffect, useRef } from "react";
import { useAuth } from "@clerk/nextjs";
import { useLanguageStore, LANGUAGE_NAMES } from "@/store/languageStore";
import { useClauseStore } from "@/store/clauseStore";
import { Clause } from "@/types/clause";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const POLL_INTERVAL_MS = 3000;

interface UseLanguageReturn {
  activeLanguage: string;
  detectedLanguage: string | null;
  detectedLanguageName: string | null;
  isTranslating: boolean;
  switchLanguage: (contractId: string, targetLang: string) => Promise<void>;
}

export function useLanguage(): UseLanguageReturn {
  const { getToken } = useAuth();
  const {
    activeLanguage,
    detectedLanguage,
    detectedLanguageName,
    isTranslating,
    translationTaskId,
    switchLanguage: storeSwitch,
    setTranslating,
    setTranslationTaskId,
  } = useLanguageStore();

  const pollTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const pollContractIdRef = useRef<string | null>(null);
  const pollTargetLangRef = useRef<string | null>(null);

  // Stop polling on unmount
  useEffect(() => {
    return () => {
      if (pollTimerRef.current) clearInterval(pollTimerRef.current);
    };
  }, []);

  /**
   * Poll for translation completion by checking if translated clauses are available.
   * We re-fetch the clauses endpoint after each interval and check if translated fields exist.
   */
  const startPolling = useCallback(
    async (contractId: string, targetLang: string) => {
      if (pollTimerRef.current) clearInterval(pollTimerRef.current);

      pollContractIdRef.current = contractId;
      pollTargetLangRef.current = targetLang;

      pollTimerRef.current = setInterval(async () => {
        try {
          const token = await getToken();
          // Re-fetch clauses to check if translated fields now exist
          const response = await fetch(
            `${API_URL}/api/v1/contracts/${contractId}/clauses`,
            {
              headers: { Authorization: `Bearer ${token}` },
            }
          );

          if (!response.ok) return;

          const clauses: Clause[] = await response.json();

          // Check if any clause has translated fields
          const hasTranslation = clauses.some(
            (c) => c.plain_english_translated || c.headline_translated
          );

          if (hasTranslation) {
            // Translation done — update store and stop polling
            if (pollTimerRef.current) clearInterval(pollTimerRef.current);
            useClauseStore.getState().setTranslatedClauses(clauses);
            setTranslating(false);
            setTranslationTaskId(null);
            storeSwitch(targetLang);
          }
        } catch (err) {
          console.error("Translation poll error:", err);
        }
      }, POLL_INTERVAL_MS);
    },
    [getToken, setTranslating, setTranslationTaskId, storeSwitch]
  );

  const switchLanguage = useCallback(
    async (contractId: string, targetLang: string) => {
      // Switching to English — just toggle without translation request
      if (targetLang === "en") {
        storeSwitch("en");
        return;
      }

      // Already translating or already in target language
      if (isTranslating || activeLanguage === targetLang) return;

      try {
        const token = await getToken();
        setTranslating(true);
        storeSwitch(targetLang);

        const response = await fetch(
          `${API_URL}/api/v1/translate/${contractId}`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify({ target_language: targetLang }),
          }
        );

        if (!response.ok) {
          throw new Error(`Translate request failed: ${response.status}`);
        }

        const data = await response.json();
        const taskId = data.task_id;

        if (taskId) {
          setTranslationTaskId(taskId);
        }

        // Start polling for completion
        await startPolling(contractId, targetLang);
      } catch (err) {
        console.error("switchLanguage error:", err);
        setTranslating(false);
        storeSwitch("en"); // revert to English on error
      }
    },
    [
      activeLanguage,
      isTranslating,
      getToken,
      setTranslating,
      setTranslationTaskId,
      storeSwitch,
      startPolling,
    ]
  );

  return {
    activeLanguage,
    detectedLanguage,
    detectedLanguageName,
    isTranslating,
    switchLanguage,
  };
}
