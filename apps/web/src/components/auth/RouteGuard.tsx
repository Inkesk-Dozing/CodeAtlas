'use client';

import { useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuthStore } from '@/stores/authStore';
import { Loader2 } from 'lucide-react';

export interface RouteGuardProps {
  children: React.ReactNode;
  isAuthenticated?: boolean;
  isLoading?: boolean;
}

export function RouteGuard({
  children,
  isAuthenticated: propIsAuthenticated,
  isLoading: propIsLoading,
}: RouteGuardProps) {
  const router = useRouter();
  const pathname = usePathname();
  const storeIsAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const storeIsLoading = useAuthStore((s) => s.isLoading);
  const checkAuth = useAuthStore((s) => s.checkAuth);

  const isAuthenticated =
    propIsAuthenticated !== undefined
      ? propIsAuthenticated
      : (storeIsAuthenticated ?? useAuthStore.getState().isAuthenticated);

  const isLoading =
    propIsLoading !== undefined
      ? propIsLoading
      : (storeIsLoading ?? useAuthStore.getState().isLoading);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      const redirectTarget = encodeURIComponent(pathname);
      router.replace(`/login?redirect=${redirectTarget}`);
    }
  }, [isLoading, isAuthenticated, router, pathname]);

  if (isLoading) {
    return (
      <div
        className="flex h-screen w-screen items-center justify-center bg-background"
        data-testid="auth-loading-state"
      >
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <span className="text-sm font-medium text-muted-foreground">Verifying session...</span>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return <>{children}</>;
}
