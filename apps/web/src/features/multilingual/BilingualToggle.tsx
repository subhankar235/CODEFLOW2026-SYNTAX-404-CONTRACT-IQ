"use client";

import { Loader2, Languages } from "lucide-react";
import { useLanguageStore, LANGUAGE_NAMES } from "@/store/languageStore";
import { useLanguage } from "@/hooks/useLanguage";
import { cn } from "@/lib/utils";

interface BilingualToggleProps {
  contractId: string;
}

export function BilingualToggle({ contractId }: BilingualToggleProps) {
  const { detectedLanguage, activeLanguage, isTranslating } = useLanguageStore();
  const { switchLanguage } = useLanguage();

  // Only show when a non-English language has been detected
  if (!detectedLanguage || detectedLanguage.toLowerCase().startsWith("en")) {
    return null;
  }

  const detectedLangCode = detectedLanguage.toLowerCase();
  const detectedLangName =
    LANGUAGE_NAMES[detectedLangCode] || detectedLanguage.toUpperCase();

  const handleSwitch = async (lang: string) => {
    if (isTranslating || activeLanguage === lang) return;
    await switchLanguage(contractId, lang);
  };

  return (
    <div className="flex items-center gap-1 rounded-lg border border-zinc-700 bg-zinc-900/80 p-0.5">
      {/* English option */}
      <button
        onClick={() => handleSwitch("en")}
        className={cn(
          "flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-all",
          activeLanguage === "en"
            ? "bg-zinc-700 text-zinc-100 shadow-sm"
            : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800"
        )}
        disabled={isTranslating}
      >
        <span className="text-[10px]">🇬🇧</span>
        English
      </button>

      {/* Detected language option */}
      <button
        onClick={() => handleSwitch(detectedLangCode)}
        className={cn(
          "flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-all",
          activeLanguage === detectedLangCode
            ? "bg-blue-600 text-white shadow-sm"
            : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800"
        )}
        disabled={isTranslating}
      >
        {isTranslating && activeLanguage === detectedLangCode ? (
          <Loader2 className="h-3 w-3 animate-spin" />
        ) : (
          <Languages className="h-3 w-3" />
        )}
        {detectedLangName}
      </button>
    </div>
  );
}
