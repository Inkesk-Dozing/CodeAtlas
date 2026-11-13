import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useAuthStore, type UserProfile } from './authStore';
import { api } from '@/lib/api/client';

// Mock client api
vi.mock('@/lib/api/client', async () => {
  let mockToken: string | null = null;
  return {
    getAccessToken: vi.fn(() => mockToken),
    setAccessToken: vi.fn((token: string | null) => {
      mockToken = token;
    }),
    registerRefreshHandler: vi.fn(),
    api: {
      auth: {
        me: vi.fn(),
        refresh: vi.fn(),
        callback: vi.fn(),
      },
    },
  };
});

describe('useAuthStore', () => {
  const sampleUser: UserProfile = {
    id: 'usr-123',
    github_id: 998877,
    username: 'octocat',
    name: 'The Octocat',
    email: 'octocat@github.com',
    avatar_url: 'https://avatars.githubusercontent.com/u/998877',
  };

  beforeEach(() => {
    vi.clearAllMocks();
    useAuthStore.setState({
      user: null,
      organizations: [],
      activeOrgId: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    });
  });

  it('sets authentication state correctly via setAuth', () => {
    useAuthStore.getState().setAuth({
      user: sampleUser,
      accessToken: 'jwt-access-token-123',
      refreshToken: 'jwt-refresh-token-456',
      organizations: [{ id: 'org-1', name: 'CodeAtlas Org', role: 'owner' }],
    });

    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(true);
    expect(state.user?.username).toBe('octocat');
    expect(state.accessToken).toBe('jwt-access-token-123');
    expect(state.refreshToken).toBe('jwt-refresh-token-456');
    expect(state.activeOrgId).toBe('org-1');
  });

  it('fetches profile during login flow', async () => {
    vi.mocked(api.auth.me).mockResolvedValueOnce(sampleUser);

    await useAuthStore.getState().login({
      access_token: 'login-token-abc',
      refresh_token: 'refresh-token-xyz',
    });

    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(true);
    expect(state.accessToken).toBe('login-token-abc');
    expect(state.user?.username).toBe('octocat');
    expect(api.auth.me).toHaveBeenCalledTimes(1);
  });

  it('clears state upon logout', () => {
    useAuthStore.getState().setAuth({
      user: sampleUser,
      accessToken: 'active-token',
      refreshToken: 'active-refresh',
    });

    useAuthStore.getState().logout();

    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(false);
    expect(state.user).toBeNull();
    expect(state.accessToken).toBeNull();
    expect(state.refreshToken).toBeNull();
  });

  it('handles silent token refresh successfully', async () => {
    useAuthStore.getState().setAuth({
      user: sampleUser,
      accessToken: 'expired-access-token',
      refreshToken: 'valid-refresh-token',
    });

    vi.mocked(api.auth.refresh).mockResolvedValueOnce({
      access_token: 'new-fresh-access-token',
      refresh_token: 'new-fresh-refresh-token',
    });

    const refreshed = await useAuthStore.getState().refreshSession();

    expect(refreshed).toBe(true);
    expect(api.auth.refresh).toHaveBeenCalledWith('valid-refresh-token');
    const state = useAuthStore.getState();
    expect(state.accessToken).toBe('new-fresh-access-token');
    expect(state.refreshToken).toBe('new-fresh-refresh-token');
  });

  it('fails refreshSession gracefully and logs out if refresh call fails', async () => {
    useAuthStore.getState().setAuth({
      user: sampleUser,
      accessToken: 'expired-access-token',
      refreshToken: 'bad-refresh-token',
    });

    vi.mocked(api.auth.refresh).mockRejectedValueOnce(new Error('Invalid token'));

    const refreshed = await useAuthStore.getState().refreshSession();

    expect(refreshed).toBe(false);
    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(false);
    expect(state.user).toBeNull();
  });
});
