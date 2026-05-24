"use client";

import { useState } from "react";
import { Languages } from "lucide-react";
import { cn } from "@/lib/utils";

interface TranslatedClauseViewProps {
  originalText: string;
  translatedText: string;
  originalLang: string;
}

export function TranslatedClauseView({ originalText, translatedText, originalLang }: TranslatedClauseViewProps) {
  const [showOriginal, setShowOriginal] = useState(false);

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          {showOriginal ? `Original (${originalLang.toUpperCase()})` : "Translated (EN)"}
        </h4>
        <button
          onClick={() => setShowOriginal(!showOriginal)}
          className="flex items-center gap-1.5 text-xs font-medium text-primary hover:underline"
        >
          <Languages className="h-3 w-3" />
          {showOriginal ? "View Translation" : "View Original"}
        </button>
      </div>
      
      <div className={cn(
        "rounded-md p-3 text-sm leading-relaxed border transition-colors",
        showOriginal ? "bg-muted/30 text-muted-foreground" : "bg-card text-foreground"
      )}>
        {showOriginal ? originalText : translatedText}
      </div>
    </div>
  );
}
