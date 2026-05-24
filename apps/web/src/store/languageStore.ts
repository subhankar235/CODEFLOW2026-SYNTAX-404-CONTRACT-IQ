import { create } from "zustand";

interface LanguageState {
  activeLanguage: string;
  detectedLanguage: string | null;
  detectedLanguageName: string | null;
  isTranslating: boolean;
  translationTaskId: string | null;
  setDetectedLanguage: (language: string | null, languageName?: string | null) => void;
  switchLanguage: (language: string) => void;
  setTranslating: (translating: boolean) => void;
  setTranslationTaskId: (taskId: string | null) => void;
  reset: () => void;
}

export const useLanguageStore = create<LanguageState>()((set) => ({
  activeLanguage: "en",
  detectedLanguage: null,
  detectedLanguageName: null,
  isTranslating: false,
  translationTaskId: null,
  setDetectedLanguage: (language, languageName) =>
    set({ detectedLanguage: language, detectedLanguageName: languageName ?? null }),
  switchLanguage: (language) => set({ activeLanguage: language }),
  setTranslating: (translating) => set({ isTranslating: translating }),
  setTranslationTaskId: (taskId) => set({ translationTaskId: taskId }),
  reset: () =>
    set({
      activeLanguage: "en",
      detectedLanguage: null,
      detectedLanguageName: null,
      isTranslating: false,
      translationTaskId: null,
    }),
}));

// Language code to display name mapping
export const LANGUAGE_NAMES: Record<string, string> = {
  en: "English",
  es: "Español",
  fr: "Français",
  de: "Deutsch",
  pt: "Português",
  hi: "हिन्दी",
  zh: "中文",
  ja: "日本語",
  ar: "العربية",
  ru: "Русский",
};