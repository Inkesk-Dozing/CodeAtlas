import { describe, it, expect, vi } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { IssueDetailDrawer } from './IssueDetailDrawer';
import { useGraphStore } from '@/stores/graphStore';
import type { CodeMapping, IssueResponse } from '@/lib/api/client';

describe('IssueDetailDrawer Integration', () => {
  const sampleIssue: IssueResponse = {
    id: 'issue-1',
    repo_id: 'repo-test',
    number: 42,
    title: 'Fix JWT expiration handling in session refresh endpoint',
    body: 'When JWT expires, user should receive 401 instead of 500 error.',
    state: 'open',
    labels: ['bug', 'security'],
    assignees: ['alice'],
    author: 'developer-bob',
    url: 'https://github.com/Inkesk-Dozing/CodeAtlas/issues/42',
    closed_at: null,
  };

  const sampleMappings: CodeMapping[] = [
    {
      node: {
        id: 'node-auth-service',
        name: 'AuthService',
        path: 'apps/api/services/auth.py',
        type: 'service',
      },
      confidence: 0.92,
      confidence_tier: 'high',
      evidence: {
        semantic_match: true,
        structural_match: true,
        historical_match: true,
        propagation_match: false,
        matched_keywords: ['jwt', 'expiration', 'refresh'],
        matched_patterns: [],
      },
      suggested_actions: [
        'Inspect JWT expiration logic in line 42-65',
        'Add unit test coverage for token refresh',
      ],
    },
    {
      node: {
        id: 'node-auth-router',
        name: 'auth_router',
        path: 'apps/api/routers/auth.py',
        type: 'route',
      },
      confidence: 0.74,
      confidence_tier: 'medium',
      evidence: {
        semantic_match: true,
        structural_match: false,
        historical_match: false,
        propagation_match: true,
        matched_keywords: ['token'],
        matched_patterns: ['reachable from top candidate (1-hop propagated)'],
      },
      suggested_actions: ['Inspect route handler for the reported behavior'],
    },
  ];

  it('renders issue metadata, author, github link, and intent pill', () => {
    const html = renderToStaticMarkup(
      <IssueDetailDrawer
        repoId="repo-test"
        issue={sampleIssue}
        mappings={sampleMappings}
        onClose={vi.fn()}
      />,
    );

    expect(html).toContain('data-testid="issue-detail-drawer"');
    expect(html).toContain('#42');
    expect(html).toContain('Fix JWT expiration handling in session refresh endpoint');
    expect(html).toContain('developer-bob');
    expect(html).toContain('Bug Fix');
    expect(html).toContain('href="https://github.com/Inkesk-Dozing/CodeAtlas/issues/42"');
    expect(html).toContain('data-testid="issue-github-link"');
  });

  it('renders ranked list of mapped files with confidence badges', () => {
    const html = renderToStaticMarkup(
      <IssueDetailDrawer
        repoId="repo-test"
        issue={sampleIssue}
        mappings={sampleMappings}
        onClose={vi.fn()}
      />,
    );

    expect(html).toContain('data-testid="mapped-file-node-auth-service"');
    expect(html).toContain('AuthService');
    expect(html).toContain('apps/api/services/auth.py');
    expect(html).toContain('92% HIGH');

    expect(html).toContain('data-testid="mapped-file-node-auth-router"');
    expect(html).toContain('auth_router');
    expect(html).toContain('74% MEDIUM');
  });

  it('renders evidence tags and suggested actions in expanded view', () => {
    const html = renderToStaticMarkup(
      <IssueDetailDrawer
        repoId="repo-test"
        issue={sampleIssue}
        mappings={sampleMappings}
        onClose={vi.fn()}
      />,
    );

    // Top item is auto-expanded
    expect(html).toContain('data-testid="expanded-reasoning-node-auth-service"');
    expect(html).toContain('Semantic Match');
    expect(html).toContain('Structural Match: AuthService');
    expect(html).toContain('Historical Reviewer Verified');
    expect(html).toContain('Inspect JWT expiration logic in line 42-65');
  });

  it('renders thumbs up / thumbs down feedback buttons', () => {
    const html = renderToStaticMarkup(
      <IssueDetailDrawer
        repoId="repo-test"
        issue={sampleIssue}
        mappings={sampleMappings}
        onClose={vi.fn()}
      />,
    );

    expect(html).toContain('data-testid="feedback-relevant-node-auth-service"');
    expect(html).toContain('data-testid="feedback-irrelevant-node-auth-service"');
    expect(html).toContain('Helpful');
  });

  it('highlights mapped subgraph in under 100ms in graphStore', () => {
    const start = performance.now();
    useGraphStore.getState().setMappedNodes(['node-auth-service', 'node-auth-router']);
    const elapsed = performance.now() - start;

    expect(useGraphStore.getState().mappedNodeIds.has('node-auth-service')).toBe(true);
    expect(useGraphStore.getState().mappedNodeIds.has('node-auth-router')).toBe(true);
    // Acceptance criteria: < 100ms
    expect(elapsed).toBeLessThan(100);
  });
});
