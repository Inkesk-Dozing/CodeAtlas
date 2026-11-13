import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { RouteGuard } from './RouteGuard';

// Mock next/navigation
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    replace: vi.fn(),
    push: vi.fn(),
  }),
  usePathname: () => '/repos/repo-1/graph',
}));

describe('RouteGuard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading spinner while authentication check is pending', () => {
    const html = renderToStaticMarkup(
      <RouteGuard isLoading={true} isAuthenticated={false}>
        <div data-testid="protected-content">Protected Content</div>
      </RouteGuard>,
    );

    expect(html).toContain('data-testid="auth-loading-state"');
    expect(html).toContain('Verifying session...');
    expect(html).not.toContain('Protected Content');
  });

  it('renders protected child content when authenticated', () => {
    const html = renderToStaticMarkup(
      <RouteGuard isLoading={false} isAuthenticated={true}>
        <div data-testid="protected-content">Protected Architecture Canvas</div>
      </RouteGuard>,
    );

    expect(html).toContain('Protected Architecture Canvas');
    expect(html).not.toContain('Verifying session...');
  });

  it('renders null when not authenticated and not loading', () => {
    const html = renderToStaticMarkup(
      <RouteGuard isLoading={false} isAuthenticated={false}>
        <div data-testid="protected-content">Protected Content</div>
      </RouteGuard>,
    );

    expect(html).toBe('');
  });
});
