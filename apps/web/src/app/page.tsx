import Link from 'next/link';
import { ArrowRight, GitBranch, Layers, MessageSquare, Search } from 'lucide-react';

const features = [
  {
    icon: Layers,
    title: 'Interactive Architecture Graph',
    description: 'Visual node-based graph of your entire monorepo with dependencies, routes, and components.',
  },
  {
    icon: GitBranch,
    title: 'Issue-to-Code Mapping',
    description: 'Click a GitHub Issue and see exactly which files, routes, and models need changes.',
  },
  {
    icon: Search,
    title: 'Semantic Code Search',
    description: 'Ask natural language questions like "Where is the auth middleware?" and get answers.',
  },
  {
    icon: MessageSquare,
    title: 'AI Codebase Chat',
    description: 'Chat with your codebase. Get explanations with citations to specific files.',
  },
];

export default function HomePage() {
  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
              <Layers className="h-5 w-5" />
            </div>
            <span className="text-xl font-bold">CodeAtlas</span>
          </div>
          <div className="flex items-center gap-4">
            <Link href="/login" className="text-sm font-medium text-muted-foreground hover:text-foreground">
              Sign in
            </Link>
            <Link
              href="/login"
              className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
            >
              Get Started
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </header>

      <main>
        <section className="mx-auto max-w-7xl px-4 py-24 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-3xl text-center">
            <h1 className="text-4xl font-bold tracking-tight sm:text-6xl">
              Understand any codebase in{' '}
              <span className="text-primary">hours, not weeks</span>
            </h1>
            <p className="mt-6 text-lg leading-8 text-muted-foreground">
              CodeAtlas automatically maps your monorepo architecture, connects GitHub Issues to the exact
              code that needs changing, and lets you query your codebase in natural language.
            </p>
            <div className="mt-10 flex items-center justify-center gap-4">
              <Link
                href="/login"
                className="inline-flex items-center gap-2 rounded-lg bg-primary px-6 py-3 text-base font-medium text-primary-foreground hover:bg-primary/90"
              >
                Connect GitHub
                <ArrowRight className="h-5 w-5" />
              </Link>
            </div>
          </div>

          <div className="mt-24 grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
            {features.map((feature) => (
              <div
                key={feature.title}
                className="rounded-xl border border-border bg-card p-6 transition-colors hover:border-primary/50"
              >
                <feature.icon className="h-8 w-8 text-primary" />
                <h3 className="mt-4 text-lg font-semibold">{feature.title}</h3>
                <p className="mt-2 text-sm text-muted-foreground">{feature.description}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="border-t border-border bg-muted/50">
          <div className="mx-auto max-w-7xl px-4 py-24 sm:px-6 lg:px-8">
            <div className="mx-auto max-w-2xl text-center">
              <h2 className="text-3xl font-bold">Built for monorepos</h2>
              <p className="mt-4 text-lg text-muted-foreground">
                Purpose-built for Turborepo, pnpm workspaces, and Nx. Understand packages, shared libraries,
                and inter-service dependencies at a glance.
              </p>
            </div>
            <div className="mt-16 grid gap-8 sm:grid-cols-3">
              {[
                { label: 'Onboarding Time', value: 'Weeks → Hours' },
                { label: 'Issue Resolution', value: '40% Faster' },
                { label: 'Graph Nodes', value: '2000+ at 60fps' },
              ].map((stat) => (
                <div key={stat.label} className="text-center">
                  <div className="text-4xl font-bold text-primary">{stat.value}</div>
                  <div className="mt-2 text-sm text-muted-foreground">{stat.label}</div>
                </div>
              ))}
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t border-border">
        <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
          <p className="text-center text-sm text-muted-foreground">
            © 2026 CodeAtlas. AI-Augmented Monorepo Onboarding Engine.
          </p>
        </div>
      </footer>
    </div>
  );
}
