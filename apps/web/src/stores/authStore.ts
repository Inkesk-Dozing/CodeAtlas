import { create } from 'zustand';
import { api, setAccessToken, registerRefreshHandler } from '@/lib/api/client';

export interface UserProfile {
  id: string;
  github_id: number;
  username: string;
  email: string | null;
  avatar_url: string | null;
  name: string | null;
  created_at?: string;
}

export interface Organization {
  id: string;
  name: string;
  role: string;
}

interface AuthState {
  user: UserProfile | null;
  organizations: Organization[];
  activeOrgId: string | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  setAuth: (data: {
    user: UserProfile;
    accessToken: string;
    refreshToken?: string | null;
    organizations?: Organization[];
  }) => void;
  setUser: (user: UserProfile | null) => void;
  setActiveOrgId: (orgId: string | null) => void;
  login: (tokens: { access_token: string; refresh_token: string }) => Promise<void>;
  logout: () => void;
  refreshSession: () => Promise<boolean>;
  checkAuth: () => Promise<boolean>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  organizations: [],
  activeOrgId: null,
  accessToken: null,
  refreshToken: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,

  setAuth: ({ user, accessToken, refreshToken = null, organizations = [] }) => {
    setAccessToken(accessToken);
    set({
      user,
      accessToken,
      refreshToken: refreshToken ?? get().refreshToken,
      organizations,
      activeOrgId: organizations[0]?.id ?? null,
      isAuthenticated: true,
      isLoading: false,
      error: null,
    });
  },

  setUser: (user) => set({ user, isAuthenticated: !!user }),

  setActiveOrgId: (activeOrgId) => set({ activeOrgId }),

  login: async ({ access_token, refresh_token }) => {
    setAccessToken(access_token);
    set({
      accessToken: access_token,
      refreshToken: refresh_token,
      isAuthenticated: true,
      isLoading: true,
      error: null,
    });

    try {
      const user = (await api.auth.me()) as UserProfile;
      set({
        user,
        isLoading: false,
      });
    } catch (err) {
      set({
        isLoading: false,
        error: err instanceof Error ? err.message : 'Failed to fetch user profile',
      });
    }
  },

  logout: () => {
    setAccessToken(null);
    set({
      user: null,
      organizations: [],
      activeOrgId: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    });
    if (typeof window !== 'undefined') {
      window.location.href = '/login';
    }
  },

  refreshSession: async () => {
    const { refreshToken } = get();
    if (!refreshToken) {
      return false;
    }

    try {
      const res = await api.auth.refresh(refreshToken);
      if (res?.access_token) {
        setAccessToken(res.access_token);
        set({
          accessToken: res.access_token,
          refreshToken: res.refresh_token || refreshToken,
          isAuthenticated: true,
        });
        return true;
      }
      return false;
    } catch {
      get().logout();
      return false;
    }
  },

  checkAuth: async () => {
    set({ isLoading: true });
    try {
      const user = (await api.auth.me()) as UserProfile;
      if (user?.id) {
        set({
          user,
          isAuthenticated: true,
          isLoading: false,
        });
        return true;
      }
      set({ isAuthenticated: false, isLoading: false, user: null });
      return false;
    } catch {
      // Try refresh if available
      const refreshed = await get().refreshSession();
      if (refreshed) {
        try {
          const user = (await api.auth.me()) as UserProfile;
          set({ user, isAuthenticated: true, isLoading: false });
          return true;
        } catch {
          set({ isAuthenticated: false, isLoading: false, user: null });
          return false;
        }
      }
      set({ isAuthenticated: false, isLoading: false, user: null });
      return false;
    }
  },
}));

// Automatically register silent refresh interceptor with API client
if (typeof window !== 'undefined') {
  registerRefreshHandler({
    onRefresh: async () => {
      const success = await useAuthStore.getState().refreshSession();
      return success ? useAuthStore.getState().accessToken : null;
    },
    onUnauthorized: () => {
      useAuthStore.getState().logout();
    },
  });
}
