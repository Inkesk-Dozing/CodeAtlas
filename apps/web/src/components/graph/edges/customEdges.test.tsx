import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import { Position, ReactFlowProvider } from '@xyflow/react';
import {
  BaseEdge,
  BezierEdge,
  SmoothStepEdge,
  customEdgeTypes,
  getEdgeStyle,
} from './index';

const renderWithProvider = (element: React.ReactElement) =>
  renderToStaticMarkup(<ReactFlowProvider>{element}</ReactFlowProvider>);

const mockEdgeProps = {
  id: 'e1-2',
  source: 'node-1',
  target: 'node-2',
  sourceX: 100,
  sourceY: 100,
  targetX: 300,
  targetY: 100,
  sourcePosition: Position.Right,
  targetPosition: Position.Left,
  selected: false,
};

describe('Typed Edge Rendering & Data Flow (Issue #44)', () => {
  describe('Edge Styles & Color Mapping', () => {
    it('styles imports as subtle slate gray solid line', () => {
      const style = getEdgeStyle('imports');
      expect(style.color).toBe('#64748B');
      expect(style.dash).toBe('none');
      expect(style.width).toBe(1.5);
      expect(style.pathType).toBe('smoothstep');

      const html = renderWithProvider(
        <BaseEdge
          {...mockEdgeProps}
          data={{
            edgeType: 'imports',
            sourceName: 'AppHeader',
            targetName: 'useUserSession',
          }}
        />
      );
      expect(html).toContain('stroke="#64748B"');
      expect(html).toContain('IMPORTS');
      expect(html).toContain('AppHeader');
      expect(html).toContain('useUserSession');
    });

    it('styles calls with electric blue directional arrow and particle animation', () => {
      const style = getEdgeStyle('calls');
      expect(style.color).toBe('#0EA5E9');
      expect(style.hasParticles).toBe(true);
      expect(style.animated).toBe(true);
      expect(style.width).toBe(2.0);

      const html = renderWithProvider(
        <BaseEdge
          {...mockEdgeProps}
          data={{
            edgeType: 'calls',
            sourceName: 'UserController',
            targetName: 'UserService',
          }}
        />
      );
      expect(html).toContain('stroke="#0EA5E9"');
      expect(html).toContain('animateMotion'); // Subtle particle flow animation along path
      expect(html).toContain('CALLS');
      expect(html).toContain('UserController');
      expect(html).toContain('UserService');
    });

    it('styles extends as emerald green dashed line', () => {
      const style = getEdgeStyle('extends');
      expect(style.color).toBe('#10B981');
      expect(style.dash).toBe('6,4');
      expect(style.width).toBe(2.0);

      const html = renderWithProvider(
        <BaseEdge
          {...mockEdgeProps}
          data={{
            edgeType: 'extends',
            sourceName: 'UserModel',
            targetName: 'BaseModel',
          }}
        />
      );
      expect(html).toContain('stroke="#10B981"');
      expect(html).toContain('stroke-dasharray="6,4"');
      expect(html).toContain('EXTENDS');
    });

    it('styles handles_route (and routes_to) as purple thick edge', () => {
      for (const routeEdge of ['handles_route', 'routes_to']) {
        const style = getEdgeStyle(routeEdge);
        expect(style.color).toBe('#A855F7');
        expect(style.width).toBe(3.0);

        const html = renderWithProvider(
          <BaseEdge
            {...mockEdgeProps}
            data={{
              edgeType: routeEdge,
              sourceName: 'GET /api/v1/users',
              targetName: 'list_users',
            }}
          />
        );
        expect(html).toContain('stroke="#A855F7"');
        expect(html).toContain('stroke-width="3"');
      }
    });

    it('styles renders as amber curved edge linking parent to child component', () => {
      const style = getEdgeStyle('renders');
      expect(style.color).toBe('#F59E0B');
      expect(style.dash).toBe('4,4');
      expect(style.width).toBe(2.0);
      expect(style.pathType).toBe('bezier');

      const html = renderWithProvider(
        <BaseEdge
          {...mockEdgeProps}
          data={{
            edgeType: 'renders',
            sourceName: 'DashboardPage',
            targetName: 'UserCard',
          }}
        />
      );
      expect(html).toContain('stroke="#F59E0B"');
      expect(html).toContain('stroke-dasharray="4,4"');
      expect(html).toContain('RENDERS');
    });
  });

  describe('Edge Highlighting and Dimming Unrelated Edges', () => {
    it('dims unrelated edges with opacity: 0.15 when isDimmed is true', () => {
      const html = renderWithProvider(
        <BaseEdge
          {...mockEdgeProps}
          data={{
            edgeType: 'imports',
            isDimmed: true,
          }}
        />
      );
      expect(html).toContain('opacity="0.15"');
      expect(html).not.toContain('animateMotion'); // Particles disabled on dimmed edges
    });

    it('highlights active edge with full opacity, thicker stroke, and glow filter', () => {
      const html = renderWithProvider(
        <BaseEdge
          {...mockEdgeProps}
          data={{
            edgeType: 'calls',
            isHighlighted: true,
          }}
        />
      );
      expect(html).toContain('opacity="1"');
      expect(html).toContain('drop-shadow-[0_0_5px_currentColor]');
      expect(html).toContain('animateMotion');
    });
  });

  describe('Edge Tooltips with Caller / Callee Context', () => {
    it('renders hover tooltip with caller and callee labels and interaction count', () => {
      const html = renderWithProvider(
        <BaseEdge
          {...mockEdgeProps}
          data={{
            edgeType: 'calls',
            sourceName: 'AuthService',
            targetName: 'TokenProvider',
            count: 3,
            isAggregated: true,
          }}
        />
      );

      // Label badge
      expect(html).toContain('CALLS');
      expect(html).toContain('(3)');

      // Tooltip content
      expect(html).toContain('AuthService');
      expect(html).toContain('TokenProvider');
      expect(html).toContain('Caller:');
      expect(html).toContain('Callee:');
      expect(html).toContain('3 connections');
    });
  });

  describe('Zoom Throttling for Fast Navigation', () => {
    it('renders fast straight SVG line when isThrottled is true', () => {
      const html = renderWithProvider(
        <BaseEdge
          {...mockEdgeProps}
          data={{
            edgeType: 'calls',
            isThrottled: true,
          }}
        />
      );
      expect(html).toContain('<line');
      expect(html).not.toContain('<path');
      expect(html).not.toContain('animateMotion');
    });
  });

  describe('Edge Types Registration', () => {
    it('exports all custom edge variants and aliases', () => {
      expect(customEdgeTypes).toHaveProperty('base');
      expect(customEdgeTypes).toHaveProperty('flow');
      expect(customEdgeTypes).toHaveProperty('bezier');
      expect(customEdgeTypes).toHaveProperty('smoothstep');
      expect(customEdgeTypes).toHaveProperty('typed');
    });

    it('SmoothStepEdge and BezierEdge render correctly', () => {
      const smoothHtml = renderWithProvider(
        <SmoothStepEdge
          {...mockEdgeProps}
          data={{ edgeType: 'extends' }}
        />
      );
      expect(smoothHtml).toContain('EXTENDS');

      const bezierHtml = renderWithProvider(
        <BezierEdge
          {...mockEdgeProps}
          data={{ edgeType: 'renders' }}
        />
      );
      expect(bezierHtml).toContain('RENDERS');
    });
  });
});
