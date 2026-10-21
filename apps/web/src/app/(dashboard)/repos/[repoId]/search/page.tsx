'use client';

import { useState, use, useCallback } from 'react';
import { Search, MessageSquare, Loader2, FileCode, Sparkles } from 'lucide-react';
import { api } from '@/lib/api/client';
import type { NodeMetadata } from '@/stores/graphStore';
import { NODE_TYPE_COLORS, NODE_TYPE_LABELS } from '@codeatlas/shared';

interface SearchResult {
  node: { id: string; type: string; name: string; path: string; metadata: NodeMetadata; summary: string | null };
  score: number;
  match_type: string;
  snippet: string | null;
}

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  citations?: { path: string; snippet: string }[];
}

export default function SearchPage({
  params,
}: {
  params: { repoId: string } | Promise<{ repoId: string }>;
}) {
  const { repoId } = use(params as Promise<{ repoId: string }>);
  const [mode, setMode] = useState<'search' | 'chat'>('search');
  const [query, setQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [tookMs, setTookMs] = useState<number | null>(null);

  const handleSearch = useCallback(
    async (e?: React.FormEvent) => {
      e?.preventDefault();
      if (!query.trim()) return;

      setIsLoading(true);
      try {
        const data = await api.search.hybrid(repoId, query, 20);
        setSearchResults(data.results as SearchResult[]);
        setTookMs(data.took_ms);
      } catch (err) {
        console.error('Search failed:', err);
      } finally {
        setIsLoading(false);
      }
    },
    [query, repoId],
  );

  const handleChat = useCallback(
    async (e?: React.FormEvent) => {
      e?.preventDefault();
      if (!query.trim()) return;

      const userMsg: ChatMessage = { role: 'user', content: query };
      setChatMessages((prev) => [...prev, userMsg]);
      setQuery('');
      setIsLoading(true);

      try {
        const data = await api.chat.ask(repoId, userMsg.content);
        const assistantMsg: ChatMessage = {
          role: 'assistant',
          content: data.answer,
          citations: data.citations,
        };
        setChatMessages((prev) => [...prev, assistantMsg]);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Unknown error';
        setChatMessages((prev) => [
          ...prev,
          { role: 'assistant', content: `Sorry, I encountered an error: ${message}` },
        ]);
      } finally {
        setIsLoading(false);
      }
    },
    [query, repoId],
  );

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="border-b border-border bg-card px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold">Search & Chat</h1>
            <p className="text-sm text-muted-foreground">
              Query your codebase in natural language
            </p>
          </div>
          <div className="flex rounded-lg border border-border p-1">
            <button
              onClick={() => setMode('search')}
              className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                mode === 'search' ? 'bg-primary text-primary-foreground' : 'text-muted-foreground'
              }`}
            >
              <Search className="h-4 w-4" />
              Search
            </button>
            <button
              onClick={() => setMode('chat')}
              className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                mode === 'chat' ? 'bg-primary text-primary-foreground' : 'text-muted-foreground'
              }`}
            >
              <MessageSquare className="h-4 w-4" />
              Chat
            </button>
          </div>
        </div>
      </div>

      {/* Input */}
      <div className="border-b border-border bg-card px-6 py-4">
        <form onSubmit={mode === 'search' ? handleSearch : handleChat}>
          <div className="flex gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder={
                  mode === 'search'
                    ? 'e.g. "authentication middleware" or "payment processing"'
                    : 'e.g. "How does the login flow work?"'
                }
                className="w-full rounded-lg border border-border bg-background py-3 pl-10 pr-4 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
            <button
              type="submit"
              disabled={isLoading || !query.trim()}
              className="rounded-lg bg-primary px-6 py-3 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
            >
              {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : mode === 'search' ? 'Search' : 'Ask'}
            </button>
          </div>
        </form>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {mode === 'search' ? (
          <>
            {tookMs !== null && searchResults.length > 0 && (
              <div className="mb-4 text-sm text-muted-foreground">
                Found {searchResults.length} results in {tookMs}ms
              </div>
            )}

            <div className="space-y-3">
              {searchResults.map((result) => (
                <div
                  key={result.node.id}
                  className="rounded-lg border border-border bg-card p-4 transition-colors hover:border-primary/50"
                >
                  <div className="flex items-start gap-3">
                    <div
                      className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-sm font-bold text-white"
                      style={{
                        backgroundColor: NODE_TYPE_COLORS[result.node.type] || '#6B7280',
                      }}
                    >
                      {result.node.type.charAt(0).toUpperCase()}
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold">{result.node.name}</span>
                        <span className="rounded bg-muted px-1.5 py-0.5 text-xs text-muted-foreground">
                          {NODE_TYPE_LABELS[result.node.type] || result.node.type}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          {Math.round(result.score * 100)}% match
                        </span>
                      </div>
                      <div className="mt-1 text-sm text-muted-foreground">{result.node.path}</div>
                      {result.snippet && (
                        <p className="mt-2 text-sm text-muted-foreground/80">{result.snippet}</p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {searchResults.length === 0 && !isLoading && query && (
              <div className="py-12 text-center text-muted-foreground">
                <FileCode className="mx-auto mb-3 h-10 w-10 opacity-50" />
                <p>No results found</p>
              </div>
            )}

            {searchResults.length === 0 && !query && (
              <div className="py-12 text-center text-muted-foreground">
                <Search className="mx-auto mb-3 h-10 w-10 opacity-50" />
                <p>Search your codebase</p>
                <p className="mt-1 text-sm">Try: &quot;authentication middleware&quot;</p>
              </div>
            )}
          </>
        ) : (
          /* Chat mode */
          <div className="mx-auto max-w-3xl space-y-4">
            {chatMessages.map((msg, i) => (
              <div
                key={i}
                className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : ''}`}
              >
                {msg.role === 'assistant' && (
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground">
                    <Sparkles className="h-4 w-4" />
                  </div>
                )}
                <div
                  className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                    msg.role === 'user'
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted'
                  }`}
                >
                  <p className="whitespace-pre-wrap text-sm leading-relaxed">{msg.content}</p>
                  {msg.citations && msg.citations.length > 0 && (
                    <div className="mt-3 space-y-1 border-t border-border/50 pt-2">
                      <div className="text-xs font-medium text-muted-foreground">Sources:</div>
                      {msg.citations.map((c, j) => (
                        <div key={j} className="text-xs text-muted-foreground">
                          <FileCode className="mr-1 inline h-3 w-3" />
                          {c.path}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="flex gap-3">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground">
                  <Sparkles className="h-4 w-4" />
                </div>
                <div className="rounded-2xl bg-muted px-4 py-3">
                  <div className="flex gap-1">
                    <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground/50 [animation-delay:0ms]" />
                    <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground/50 [animation-delay:150ms]" />
                    <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground/50 [animation-delay:300ms]" />
                  </div>
                </div>
              </div>
            )}

            {chatMessages.length === 0 && !isLoading && (
              <div className="py-12 text-center text-muted-foreground">
                <MessageSquare className="mx-auto mb-3 h-10 w-10 opacity-50" />
                <p>Ask anything about your codebase</p>
                <div className="mt-4 flex flex-wrap justify-center gap-2">
                  {[
                    'How does authentication work?',
                    'Where is the payment processing?',
                    'What are the main API routes?',
                  ].map((q) => (
                    <button
                      key={q}
                      onClick={() => setQuery(q)}
                      className="rounded-full border border-border px-3 py-1.5 text-xs hover:bg-muted"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
