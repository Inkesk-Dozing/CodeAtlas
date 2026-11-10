import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { beforeEach, describe, expect, it } from 'vitest';
import { ReactFlowProvider } from '@xyflow/react';
import type { GraphNode } from '@/stores/graphStore';
import { useGraphStore } from '@/stores/graphStore';
import { getNodeRendererType } from '@/lib/graph/clustering';
import {
  BaseNode,
  ClassNode,
  ComponentNode,
  FileNode,
  FunctionNode,
  RouteNode,
  customNodeTypes,
} from './index';

const renderWithProvider = (element: React.ReactElement) =>
  renderToStaticMarkup(<ReactFlowProvider>{element}</ReactFlowProvider>);

const mockNodeProps = {
  selected: false,
  zIndex: 0,
  isConnectable: true,
  positionAbsoluteX: 0,
  positionAbsoluteY: 0,
  dragging: false,
  selectable: true,
  deletable: false,
  draggable: true,
};

describe('Custom AST Node Renderers (Issue #43)', () => {
  beforeEach(() => {
    useGraphStore.setState({
      selectedNodeId: null,
      highlightedNodeIds: new Set(),
    });
  });

  const createMockNode = (overrides: Partial<GraphNode>): GraphNode => ({
    id: 'test-node-1',
    type: 'file',
    name: 'UserSession',
    path: 'apps/web/hooks/useUserSession.ts',
    language: 'typescript',
    metadata: {},
    summary: 'Handles user session state',
    ...overrides,
  });

  describe('FileNode', () => {
    it('renders file icon, path, line count badge, and language tag', () => {
      const node = createMockNode({
        type: 'file',
        name: 'useUserSession.ts',
        path: 'apps/web/hooks/useUserSession.ts',
        language: 'typescript',
        metadata: { loc: 142, exports: ['useUserSession', 'SessionContext'] },
      });

      const html = renderWithProvider(
        <FileNode
          id={node.id}
          data={{ node, isSelected: false, isHighlighted: false }}
          type="file"
          {...mockNodeProps}
        />
      );

      expect(html).toContain('useUserSession.ts');
      expect(html).toContain('apps/web/hooks/useUserSession.ts');
      expect(html).toContain('142 LOC');
      expect(html).toContain('TYPE');
      expect(html).toContain('2 exports');
      expect(html).toContain('react-flow__handle-left');
      expect(html).toContain('react-flow__handle-right');
    });

    it('renders neon glow when selected or highlighted', () => {
      const node = createMockNode({ id: 'file-selected' });
      const htmlSelected = renderWithProvider(
        <FileNode
          id={node.id}
          data={{ node, isSelected: true, isHighlighted: false }}
          type="file"
          {...mockNodeProps}
          selected={true}
        />
      );
      expect(htmlSelected).toContain('shadow-[0_0_16px_rgba(14,165,233,0.7)]');

      const htmlHighlighted = renderWithProvider(
        <FileNode
          id={node.id}
          data={{ node, isSelected: false, isHighlighted: true }}
          type="file"
          {...mockNodeProps}
        />
      );
      expect(htmlHighlighted).toContain('shadow-[0_0_16px_rgba(245,158,11,0.7)]');
    });
  });

  describe('FunctionNode', () => {
    it('renders parameter signature, return type, complexity pill, and async badge', () => {
      const node = createMockNode({
        type: 'function',
        name: 'fetchUserProfile',
        metadata: {
          signature: '(userId: string, opts?: FetchOpts): Promise<UserProfile>',
          is_async: true,
          complexity: { cyclomatic: 12 },
        },
      });

      const html = renderWithProvider(
        <FunctionNode
          id={node.id}
          data={{ node, isSelected: false, isHighlighted: false }}
          type="function"
          {...mockNodeProps}
        />
      );

      expect(html).toContain('fetchUserProfile');
      expect(html).toContain('async');
      expect(html).toContain('(userId: string, opts?: FetchOpts): Promise&lt;UserProfile&gt;');
      expect(html).toContain('Promise&lt;UserProfile&gt;');
      expect(html).toContain('CC 12');
      expect(html).toContain('complex');
      expect(html).toContain('react-flow__handle-left');
      expect(html).toContain('react-flow__handle-right');
    });

    it('renders low complexity without complex warning pill', () => {
      const node = createMockNode({
        type: 'function',
        name: 'simpleAdd',
        metadata: {
          signature: '(a: number, b: number): number',
          complexity: { cyclomatic: 2 },
        },
      });

      const html = renderWithProvider(
        <FunctionNode
          id={node.id}
          data={{ node, isSelected: false, isHighlighted: false }}
          type="function"
          {...mockNodeProps}
        />
      );

      expect(html).toContain('CC 2');
      expect(html).not.toContain('complex');
    });
  });

  describe('ClassNode', () => {
    it('renders class name, inheritance indicator, and methods list preview', () => {
      const node = createMockNode({
        type: 'class',
        name: 'UserService',
        metadata: {
          bases: ['BaseService', 'EventEmitter'],
          methods: ['getUser', 'createUser', 'deleteUser', 'updateUser'],
          fields: ['db', 'cache'],
          is_service: true,
        },
      });

      const html = renderWithProvider(
        <ClassNode
          id={node.id}
          data={{ node, isSelected: false, isHighlighted: false }}
          type="class"
          {...mockNodeProps}
        />
      );

      expect(html).toContain('UserService');
      expect(html).toContain('extends BaseService, EventEmitter');
      expect(html).toContain('getUser()');
      expect(html).toContain('createUser()');
      expect(html).toContain('deleteUser()');
      expect(html).toContain('+1 more method');
      expect(html).toContain('4 methods');
      expect(html).toContain('2 fields');
      expect(html).toContain('service');
      expect(html).toContain('react-flow__handle-left');
      expect(html).toContain('react-flow__handle-right');
    });
  });

  describe('RouteNode', () => {
    it('renders HTTP verb pill, URL path, and handler name', () => {
      const node = createMockNode({
        type: 'route',
        name: 'GET /api/v1/users/:id',
        metadata: {
          http_method: 'GET',
          route_path: '/api/v1/users/:id',
          controller: 'getUserById',
          framework: 'fastapi',
          params: ['id'],
        },
      });

      const html = renderWithProvider(
        <RouteNode
          id={node.id}
          data={{ node, isSelected: false, isHighlighted: false }}
          type="route"
          {...mockNodeProps}
        />
      );

      expect(html).toContain('GET');
      expect(html).toContain('/api/v1/users/:id');
      expect(html).toContain('getUserById');
      expect(html).toContain('fastapi');
      expect(html).toContain('1 param');
      expect(html).toContain('react-flow__handle-left');
      expect(html).toContain('react-flow__handle-right');
    });

    it('renders distinct verbs (POST, DELETE, PUT)', () => {
      for (const verb of ['POST', 'PUT', 'DELETE', 'PATCH']) {
        const node = createMockNode({
          type: 'route',
          metadata: { http_method: verb, route_path: `/api/${verb.toLowerCase()}` },
        });

        const html = renderWithProvider(
          <RouteNode
            id={node.id}
            data={{ node, isSelected: false, isHighlighted: false }}
            type="route"
            {...mockNodeProps}
          />
        );
        expect(html).toContain(verb);
      }
    });
  });

  describe('ComponentNode', () => {
    it('renders component name, React tag, hooks preview, and props count', () => {
      const node = createMockNode({
        type: 'component',
        name: 'UserCard',
        metadata: {
          hooks_used: ['useUserSession', 'useCallback'],
          props: ['userId', 'onSelect', 'theme'],
        },
      });

      const html = renderWithProvider(
        <ComponentNode
          id={node.id}
          data={{ node, isSelected: false, isHighlighted: false }}
          type="component"
          {...mockNodeProps}
        />
      );

      expect(html).toContain('UserCard');
      expect(html).toContain('React');
      expect(html).toContain('useUserSession');
      expect(html).toContain('useCallback');
      expect(html).toContain('2 hooks');
      expect(html).toContain('3 props');
      expect(html).toContain('react-flow__handle-left');
      expect(html).toContain('react-flow__handle-right');
    });
  });

  describe('BaseNode fallback', () => {
    it('renders generic node type badge and Left/Right handles', () => {
      const node = createMockNode({
        type: 'interface',
        name: 'IAuthToken',
      });

      const html = renderWithProvider(
        <BaseNode
          id={node.id}
          data={{ node, isSelected: false, isHighlighted: false }}
          type="base"
          {...mockNodeProps}
        />
      );

      expect(html).toContain('IAuthToken');
      expect(html).toContain('interface');
      expect(html).toContain('react-flow__handle-left');
      expect(html).toContain('react-flow__handle-right');
    });
  });

  describe('Node Selection Dispatch', () => {
    it('clicking node triggers selection in useGraphStore', () => {
      const node = createMockNode({ id: 'target-node-42' });
      expect(useGraphStore.getState().selectedNodeId).toBeNull();

      useGraphStore.getState().selectNode(node.id);
      expect(useGraphStore.getState().selectedNodeId).toBe('target-node-42');
    });
  });

  describe('Node Types Registration and Layout Mapping', () => {
    it('registers all specialized AST node types in customNodeTypes', () => {
      expect(customNodeTypes).toHaveProperty('file');
      expect(customNodeTypes).toHaveProperty('function');
      expect(customNodeTypes).toHaveProperty('class');
      expect(customNodeTypes).toHaveProperty('route');
      expect(customNodeTypes).toHaveProperty('component');
      expect(customNodeTypes).toHaveProperty('base');
      expect(customNodeTypes).toHaveProperty('cluster');
    });

    it('correctly maps node types to specialized renderers via getNodeRendererType', () => {
      expect(getNodeRendererType('file')).toBe('file');
      expect(getNodeRendererType('function')).toBe('function');
      expect(getNodeRendererType('method')).toBe('function');
      expect(getNodeRendererType('class')).toBe('class');
      expect(getNodeRendererType('model')).toBe('class');
      expect(getNodeRendererType('service')).toBe('class');
      expect(getNodeRendererType('route')).toBe('route');
      expect(getNodeRendererType('component')).toBe('component');
      expect(getNodeRendererType('interface')).toBe('base');
      expect(getNodeRendererType('variable')).toBe('base');
    });
  });
});
