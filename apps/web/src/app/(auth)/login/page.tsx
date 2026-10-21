'use client';

import { Suspense } from 'react';
import { Layers, Github } from 'lucide-react';

function LoginContent() {
  const handleGitHubLogin = () => {
    const clientId = process.env.NEXT_PUBLIC_GITHUB_CLIENT_ID || '';
    const redirectUri = `${window.location.origin}/api/auth/callback`;
    const state = Math.random().toString(36).slice(2);

    localStorage.setItem('oauth_state', state);

    const githubAuthUrl = `https://github.com/login/oauth/authorize?client_id=${clientId}&redirect_uri=${encodeURIComponent(redirectUri)}&scope=read:user&state=${state}`;

    window.location.href = githubAuthUrl;
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="w-full max-w-md">
        <div className="text-center">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-primary">
            <Layers className="h-8 w-8 text-primary-foreground" />
          </div>
          <h1 className="mt-6 text-3xl font-bold">Welcome to CodeAtlas</h1>
          <p className="mt-2 text-muted-foreground">
            AI-Augmented Monorepo Onboarding Engine
          </p>
        </div>

        <div className="mt-8 rounded-xl border border-border bg-card p-6">
          <button
            onClick={handleGitHubLogin}
            className="flex w-full items-center justify-center gap-3 rounded-lg bg-[#24292f] px-4 py-3 text-sm font-medium text-white transition-colors hover:bg-[#24292f]/90"
          >
            <Github className="h-5 w-5" />
            Continue with GitHub
          </button>

          <div className="mt-6 text-center text-xs text-muted-foreground">
            <p>
              By signing in, you agree to our{' '}
              <a href="#" className="text-primary hover:underline">
                Terms of Service
              </a>{' '}
              and{' '}
              <a href="#" className="text-primary hover:underline">
                Privacy Policy
              </a>
            </p>
          </div>
        </div>

        <div className="mt-8 space-y-4">
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t border-border" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-background px-2 text-muted-foreground">What you get</span>
            </div>
          </div>

          <div className="space-y-3">
            {[
              'Interactive architecture graphs',
              'Issue-to-code mapping with confidence scores',
              'Natural language code search',
              'AI-powered code summaries',
            ].map((feature) => (
              <div key={feature} className="flex items-center gap-2 text-sm text-muted-foreground">
                <span className="flex h-5 w-5 items-center justify-center rounded-full bg-primary/10 text-xs text-primary">
                  ✓
                </span>
                {feature}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center">Loading...</div>}>
      <LoginContent />
    </Suspense>
  );
}
