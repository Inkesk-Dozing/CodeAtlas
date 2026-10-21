import { create } from 'zustand';

type Panel = 'node-detail' | 'issue-mapping' | 'search' | 'chat' | 'summary' | null;

interface UIState {
  sidebarOpen: boolean;
  activePanel: Panel;
  rightPanelOpen: boolean;
  theme: 'light' | 'dark' | 'system';

  toggleSidebar: () => void;
  openPanel: (panel: Panel) => void;
  closePanel: () => void;
  setTheme: (theme: 'light' | 'dark' | 'system') => void;
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: true,
  activePanel: null,
  rightPanelOpen: false,
  theme: 'system',

  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),

  openPanel: (panel) =>
    set({
      activePanel: panel,
      rightPanelOpen: panel !== null,
    }),

  closePanel: () => set({ activePanel: null, rightPanelOpen: false }),

  setTheme: (theme) => {
    set({ theme });
    localStorage.setItem('theme', theme);
    const root = document.documentElement;
    root.classList.remove('light', 'dark');
    if (theme === 'system') {
      const sys = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
      root.classList.add(sys);
    } else {
      root.classList.add(theme);
    }
  },
}));
