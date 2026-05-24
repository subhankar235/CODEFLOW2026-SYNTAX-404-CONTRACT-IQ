import { create } from "zustand";
import { persist } from "zustand/middleware";

type ActivePanel = "consequence" | "counter-offer" | "precedent" | null;

interface UIState {
  isCounterOfferPanelOpen: boolean;
  isPrecedentPanelOpen: boolean;
  activePanel: ActivePanel;
  // Language banner dismiss (persisted)
  languageBannerDismissed: boolean;
  openCounterOfferPanel: () => void;
  openPrecedentPanel: () => void;
  closePanel: () => void;
  dismissLanguageBanner: () => void;
  resetLanguageBanner: () => void;
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      isCounterOfferPanelOpen: false,
      isPrecedentPanelOpen: false,
      activePanel: null,
      languageBannerDismissed: false,
      openCounterOfferPanel: () =>
        set({ isCounterOfferPanelOpen: true, activePanel: "counter-offer" }),
      openPrecedentPanel: () =>
        set({ isPrecedentPanelOpen: true, activePanel: "precedent" }),
      closePanel: () =>
        set({
          isCounterOfferPanelOpen: false,
          isPrecedentPanelOpen: false,
          activePanel: null,
        }),
      dismissLanguageBanner: () => set({ languageBannerDismissed: true }),
      resetLanguageBanner: () => set({ languageBannerDismissed: false }),
    }),
    {
      name: "ui-store",
      partialize: (state) => ({
        languageBannerDismissed: state.languageBannerDismissed,
      }),
    }
  )
);