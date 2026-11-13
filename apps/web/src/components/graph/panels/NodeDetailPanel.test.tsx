import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { NodeDetailPanel } from './NodeDetailPanel';
import { CodeSnippetPreview } from './CodeSnippetPreview';
import { useGraphStore, type GraphNode } from '@/stores/graphStore';

describe('NodeDetailPanel and CodeSnippetPreview', () => {
  const sampleNode: GraphNode = {
    id: 'node-auth-service',
    name: 'AuthService',
    type: 'class',
    path: 'apps/api/services/auth.py',
    language: 'python',
    summary: null,
    metadata: {
      language: 'python',
      line: 45,
      loc: 44,
      docstring: 'Handles JWT authentication and user token verification.',
      signature: 'class AuthService(BaseService):',
      complexity: {
        cyclomatic: 12,
        cognitive: 8,
      },
    },
  };

  const callerNode: GraphNode = {
    id: 'node-login-controller',
    name: 'LoginController',
    type: 'function',
    path: 'apps/api/controllers/auth.py',
    language: 'python',
    summary: null,
    metadata: {},
  };

  beforeEach(() => {
    vi.clearAllMocks();
    useGraphStore.setState({
      nodes: new Map([
        [sampleNode.id, sampleNode],
        [callerNode.id, callerNode],
      ]),
      edges: new Map([
        [
          'edge-1',
          {
            id: 'edge-1',
            source_id: callerNode.id,
            target_id: sampleNode.id,
            type: 'calls',
            weight: 1,
          },
        ],
      ]),
      selectedNodeId: sampleNode.id,
    });
  });

  it('renders node details: name, line range, qualified path, and action buttons', () => {
    const html = renderToStaticMarkup(<NodeDetailPanel repoId="test-repo" />);

    expect(html).toContain('data-testid="node-detail-panel"');
    expect(html).toContain('AuthService');
    expect(html).toContain('lines 45-88');
    expect(html).toContain('apps/api/services/auth.py');
    expect(html).toContain('data-testid="node-copy-path-btn"');
    expect(html).toContain('data-testid="node-github-btn"');
    expect(html).toContain('apps/api/services/auth.py#L45');
  });

  it('displays cyclomatic complexity score with risk indicator', () => {
    const html = renderToStaticMarkup(<NodeDetailPanel repoId="test-repo" />);

    // Score is 12 -> High risk
    expect(html).toContain('12');
    expect(html).toContain('High');
    expect(html).toContain('Cyclomatic');
  });

  it('renders navigation tabs for Details, Callers, Dependencies, and Summary', () => {
    const html = renderToStaticMarkup(<NodeDetailPanel repoId="test-repo" />);

    expect(html).toContain('data-testid="tab-details"');
    expect(html).toContain('data-testid="tab-callers"');
    expect(html).toContain('data-testid="tab-dependencies"');
    expect(html).toContain('data-testid="tab-summary"');
  });

  it('renders syntax-highlighted code snippet preview with line numbers', () => {
    const code = 'class AuthService:\n    def verify(token):\n        return True';
    const html = renderToStaticMarkup(
      <CodeSnippetPreview code={code} language="python" startLine={45} className="max-h-[200px]" />,
    );

    expect(html).toContain('data-testid="code-snippet-preview"');
    expect(html).toContain('45');
    expect(html).toContain('46');
    expect(html).toContain('47');
    expect(html).toContain('AuthService');
    expect(html).toContain('verify');
    expect(html).toContain('return');
  });

  it('handles empty or null selected node gracefully', () => {
    useGraphStore.setState({ selectedNodeId: null });
    const html = renderToStaticMarkup(<NodeDetailPanel repoId="test-repo" />);
    expect(html).toBe('');
  });
});
