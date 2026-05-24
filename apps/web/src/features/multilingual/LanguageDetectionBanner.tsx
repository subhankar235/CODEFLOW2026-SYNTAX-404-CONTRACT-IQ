"use client";

import { AnimatePresence, motion } from "framer-motion";
import { Globe, X, ChevronDown } from "lucide-react";
import { useState, useRef, useEffect } from "react";
import { useUIStore } from "@/store/uiStore";
import { useLanguageStore, LANGUAGE_NAMES } from "@/store/languageStore";
import { useLanguage } from "@/hooks/useLanguage";

interface LanguageDetectionBannerProps {
  contractId: string;
}

const CONTRACT_TYPES = [
  { value: "employment", label: "Employment Contract" },
  { value: "nda", label: "Non-Disclosure Agreement" },
  { value: "freelance", label: "Freelance / Contractor" },
  { value: "saas", label: "SaaS Subscription" },
  { value: "lease", label: "Lease Agreement" },
  { value: "partnership", label: "Partnership Agreement" },
  { value: "ip_license", label: "IP License" },
  { value: "loan", label: "Loan Agreement" },
  { value: "m_a", label: "M&A Agreement" },
  { value: "other", label: "Other" },
];

export function LanguageDetectionBanner({ contractId }: LanguageDetectionBannerProps) {
  const { detectedLanguage, detectedLanguageName } = useLanguageStore();
  const { languageBannerDismissed, dismissLanguageBanner } = useUIStore();
  const { switchLanguage } = useLanguage();

  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  // Don't show if dismissed, no language detected, or language is English
  const shouldShow =
    !languageBannerDismissed &&
    detectedLanguage &&
    !detectedLanguage.toLowerCase().startsWith("en");

  const languageDisplayName =
    detectedLanguageName ||
    LANGUAGE_NAMES[detectedLanguage?.toLowerCase() || ""] ||
    (detectedLanguage?.toUpperCase() ?? "Unknown");

  return (
    <AnimatePresence>
      {shouldShow && (
        <motion.div
          initial={{ y: -60, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: -60, opacity: 0 }}
          transition={{ type: "spring", stiffness: 300, damping: 28 }}
          className="relative z-30 mx-4 mb-3 overflow-visible"
        >
          <div className="flex items-center justify-between rounded-xl border border-blue-500/30 bg-blue-500/10 px-4 py-3 text-sm backdrop-blur-sm">
            {/* Left: Globe + message */}
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-500/20">
                <Globe className="h-4 w-4 text-blue-400" />
              </div>
              <div>
                <p className="font-semibold text-blue-100">
                  {languageDisplayName} contract detected
                </p>
                <p className="text-xs text-blue-300/80 mt-0.5">
                  Analyzing from employee perspective
                </p>
              </div>
            </div>

            {/* Right: Actions */}
            <div className="flex shrink-0 items-center gap-2 ml-4">
              {/* Change Language Detection dropdown */}
              <div className="relative" ref={dropdownRef}>
                <button
                  onClick={() => setDropdownOpen((p) => !p)}
                  className="flex items-center gap-1.5 rounded-lg border border-blue-500/30 bg-blue-500/10 px-3 py-1.5 text-xs font-medium text-blue-200 transition-all hover:bg-blue-500/20 hover:text-blue-100"
                >
                  Change Language Detection
                  <ChevronDown
                    className={`h-3.5 w-3.5 transition-transform ${dropdownOpen ? "rotate-180" : ""}`}
                  />
                </button>

                <AnimatePresence>
                  {dropdownOpen && (
                    <motion.div
                      initial={{ opacity: 0, y: -8, scale: 0.95 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      exit={{ opacity: 0, y: -8, scale: 0.95 }}
                      transition={{ duration: 0.15 }}
                      className="absolute right-0 top-full mt-2 w-56 rounded-xl border border-zinc-700 bg-zinc-900 shadow-xl z-50 overflow-hidden"
                    >
                      <div className="px-3 py-2 border-b border-zinc-800">
                        <p className="text-[10px] font-semibold uppercase tracking-wider text-zinc-500">
                          Override Contract Type
                        </p>
                      </div>
                      {CONTRACT_TYPES.map((ct) => (
                        <button
                          key={ct.value}
                          onClick={() => {
                            // Trigger translation with the current detected language
                            if (detectedLanguage) {
                              switchLanguage(contractId, detectedLanguage);
                            }
                            setDropdownOpen(false);
                          }}
                          className="w-full px-3 py-2 text-left text-xs text-zinc-300 hover:bg-zinc-800 hover:text-zinc-100 transition-colors"
                        >
                          {ct.label}
                        </button>
                      ))}
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              {/* Dismiss */}
              <button
                onClick={dismissLanguageBanner}
                className="flex h-7 w-7 items-center justify-center rounded-full text-blue-300/50 hover:bg-blue-500/20 hover:text-blue-200 transition-colors"
                aria-label="Dismiss"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
