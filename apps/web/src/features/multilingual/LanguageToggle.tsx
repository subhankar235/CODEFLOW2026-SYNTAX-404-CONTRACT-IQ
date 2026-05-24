"use client";

import { useState, useRef, useEffect } from "react";
import { Languages, ChevronDown } from "lucide-react";

export function LanguageToggle() {
  const [isOpen, setIsOpen] = useState(false);
  const [lang, setLang] = useState("EN");
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const toggle = () => setIsOpen((p) => !p);

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={toggle}
        className="flex items-center gap-2 rounded-md border bg-card px-3 py-1.5 text-sm font-medium transition-colors hover:bg-muted"
      >
        <Languages className="h-4 w-4 text-muted-foreground" />
        {lang}
        <ChevronDown className="h-3 w-3 text-muted-foreground" />
      </button>

      {isOpen && (
        <div className="absolute right-0 top-full mt-1 w-32 rounded-md border bg-card shadow-lg z-50 overflow-hidden">
          <button
            onClick={() => { setLang("EN"); setIsOpen(false); }}
            className="w-full px-4 py-2 text-left text-sm hover:bg-muted"
          >
            English (EN)
          </button>
          <button
            onClick={() => { setLang("ES"); setIsOpen(false); }}
            className="w-full px-4 py-2 text-left text-sm hover:bg-muted"
          >
            Spanish (ES)
          </button>
        </div>
      )}
    </div>
  );
}
