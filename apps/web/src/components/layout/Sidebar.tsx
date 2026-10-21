'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  GitBranch,
  MessageSquare,
  Settings,
  ChevronLeft,
  Layers,
} from 'lucide-react';
import { useUIStore } from '@/stores/uiStore';

interface SidebarProps {
  repoId?: string;
  repoName?: string;
}

export function Sidebar({ repoId, repoName }: SidebarProps) {
  const pathname = usePathname();
  const { sidebarOpen, toggleSidebar } = useUIStore();

  const navItems = repoId
    ? [
        { href: `/repos/${repoId}/graph`, icon: LayoutDashboard, label: 'Architecture Graph' },
        { href: `/repos/${repoId}/issues`, icon: GitBranch, label: 'Issue Mapping' },
        { href: `/repos/${repoId}/search`, icon: MessageSquare, label: 'Search & Chat' },
      ]
    : [];

  if (!sidebarOpen) {
    return (
      <div className="flex w-12 flex-col border-r border-sidebar-border bg-sidebar">
        <button
          onClick={toggleSidebar}
          className="flex h-12 items-center justify-center text-sidebar-foreground hover:bg-white/5"
        >
          <ChevronLeft className="h-4 w-4 rotate-180" />
        </button>
        <div className="flex flex-col items-center gap-1 py-2">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`rounded-md p-2 ${
                pathname === item.href
                  ? 'bg-white/10 text-white'
                  : 'text-sidebar-foreground/60 hover:bg-white/5 hover:text-white'
              }`}
              title={item.label}
            >
              <item.icon className="h-4 w-4" />
            </Link>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="flex w-60 flex-col border-r border-sidebar-border bg-sidebar text-sidebar-foreground">
      {/* Logo */}
      <div className="flex h-12 items-center justify-between border-b border-sidebar-border px-4">
        <Link href="/" className="flex items-center gap-2">
          <div className="flex h-6 w-6 items-center justify-center rounded bg-primary">
            <Layers className="h-4 w-4 text-primary-foreground" />
          </div>
          <span className="text-sm font-bold">CodeAtlas</span>
        </Link>
        <button
          onClick={toggleSidebar}
          className="rounded p-1 hover:bg-white/5"
          title="Collapse sidebar"
        >
          <ChevronLeft className="h-4 w-4" />
        </button>
      </div>

      {/* Repository info */}
      {repoName && (
        <div className="border-b border-sidebar-border px-4 py-3">
          <div className="text-xs text-sidebar-foreground/50">Repository</div>
          <div className="mt-0.5 truncate text-sm font-medium">{repoName}</div>
        </div>
      )}

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-3 py-4">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-primary/20 text-primary'
                  : 'text-sidebar-foreground/70 hover:bg-white/5 hover:text-white'
              }`}
            >
              <item.icon className="h-4 w-4 shrink-0" />
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* Bottom */}
      <div className="border-t border-sidebar-border px-3 py-3">
        <Link
          href="/repos"
          className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-sidebar-foreground/70 hover:bg-white/5 hover:text-white"
        >
          <Settings className="h-4 w-4" />
          All Repositories
        </Link>
      </div>
    </div>
  );
}
