import { describe, it, expect, vi } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { RepoCard, type RepositoryItem, STATUS_PILL_CONFIG } from './RepoCard';

// Mock useRouter from next/navigation
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
  }),
}));

describe('RepoCard', () => {
  const sampleRepo: RepositoryItem = {
    id: 'repo-codeatlas',
    name: 'CodeAtlas',
    full_name: 'Inkesk-Dozing/CodeAtlas',
    owner: 'Inkesk-Dozing',
    language: 'TypeScript',
    description: 'Autonomous Software Engineering Architecture Engine',
    status: 'ready',
    node_count: 1420,
    edge_count: 3840,
    star_count: 520,
    last_analyzed_at: '2026-11-13T10:00:00Z',
  };

  it('renders repository card with details: name, description, stars, and node count', () => {
    const html = renderToStaticMarkup(<RepoCard repo={sampleRepo} />);

    expect(html).toContain('data-testid="repo-card-repo-codeatlas"');
    expect(html).toContain('CodeAtlas');
    expect(html).toContain('Inkesk-Dozing/CodeAtlas');
    expect(html).toContain('Autonomous Software Engineering Architecture Engine');
    expect(html).toContain('TypeScript');
    expect(html).toContain('520');
    expect(html).toContain('1,420 nodes');
    expect(html).toContain('data-testid="explore-graph-btn-repo-codeatlas"');
    expect(html).toContain('/repos/repo-codeatlas/graph');
  });

  it('renders status pill with appropriate status label and styling', () => {
    const htmlReady = renderToStaticMarkup(<RepoCard repo={sampleRepo} />);
    expect(htmlReady).toContain('Ready');

    const cloningRepo: RepositoryItem = {
      ...sampleRepo,
      status: 'cloning',
    };
    const htmlCloning = renderToStaticMarkup(<RepoCard repo={cloningRepo} />);
    expect(htmlCloning).toContain('Cloning');

    const failedRepo: RepositoryItem = {
      ...sampleRepo,
      status: 'failed',
    };
    const htmlFailed = renderToStaticMarkup(<RepoCard repo={failedRepo} />);
    expect(htmlFailed).toContain('Failed');
  });

  it('disables ingest button and renders progress bar while ingesting', () => {
    const ingestingRepo: RepositoryItem = {
      ...sampleRepo,
      status: 'parsing',
    };
    const html = renderToStaticMarkup(<RepoCard repo={ingestingRepo} />);

    expect(html).toContain('Ingesting...');
    expect(html).toContain('disabled=""');
  });

  it('verifies all status pills configuration keys', () => {
    const expectedStatuses = ['ready', 'cloning', 'parsing', 'extracting', 'embedding', 'failed'];
    expectedStatuses.forEach((status) => {
      expect(STATUS_PILL_CONFIG[status]).toBeDefined();
      expect(STATUS_PILL_CONFIG[status].label).toBeDefined();
    });
  });
});
