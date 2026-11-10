export * from './types';
export * from './BaseNode';
export * from './ClusterNode';
export * from './FileNode';
export * from './FunctionNode';
export * from './ClassNode';
export * from './RouteNode';
export * from './ComponentNode';

import { BaseNode } from './BaseNode';
import { ClusterNode } from './ClusterNode';
import { FileNode } from './FileNode';
import { FunctionNode } from './FunctionNode';
import { ClassNode } from './ClassNode';
import { RouteNode } from './RouteNode';
import { ComponentNode } from './ComponentNode';

export const customNodeTypes = {
  base: BaseNode,
  cluster: ClusterNode,
  file: FileNode,
  function: FunctionNode,
  class: ClassNode,
  route: RouteNode,
  component: ComponentNode,
};
