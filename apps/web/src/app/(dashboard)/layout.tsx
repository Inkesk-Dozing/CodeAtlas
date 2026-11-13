'use client';

import { Sidebar } from '@/components/layout/Sidebar';
import { RouteGuard } from '@/components/auth/RouteGuard';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <RouteGuard>
      <div className="flex h-screen overflow-hidden bg-background">
        <Sidebar />
        <main className="flex-1 overflow-hidden">{children}</main>
      </div>
    </RouteGuard>
  );
}
