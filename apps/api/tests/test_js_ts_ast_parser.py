"""Unit tests for JavaScript & TypeScript AST Parser Engine (Issue #25)."""

import pytest

from parsers.javascript import JavaScriptParser


@pytest.fixture
def parser() -> JavaScriptParser:
    return JavaScriptParser()


def test_esm_and_commonjs_imports_with_classification(parser: JavaScriptParser):
    code = """
import React, { useState, useEffect as useEff } from 'react';
import * as lodash from 'lodash';
import { Button } from '@/components/Button';
import { AppHeader } from '~/layout/AppHeader';
import { CoreService } from '@repo/core';
import { UITheme } from '@workspace/theme';
import { helper } from './utils';
import { config } from '../config';

const express = require('express');
const { json, urlencoded } = require('body-parser');
const localAuth = require('./auth');
const sharedUtil = require('@shared/utils');
"""
    result = parser.parse(code, "src/index.ts")
    imports = result.imports
    import_sources = {imp.source: imp for imp in imports}

    # Third-party imports
    assert "react" in import_sources
    assert import_sources["react"].is_third_party is True
    assert import_sources["react"].is_internal is False
    assert "useState" in import_sources["react"].names

    assert "lodash" in import_sources
    assert import_sources["lodash"].is_third_party is True
    assert import_sources["lodash"].is_namespace is True

    assert "express" in import_sources
    assert import_sources["express"].is_third_party is True

    assert "body-parser" in import_sources
    assert import_sources["body-parser"].is_third_party is True
    assert "json" in import_sources["body-parser"].names

    # Internal relative imports
    assert "./utils" in import_sources
    assert import_sources["./utils"].is_internal is True
    assert import_sources["./utils"].is_monorepo is False
    assert import_sources["./utils"].is_third_party is False

    assert "../config" in import_sources
    assert import_sources["../config"].is_internal is True
    assert import_sources["../config"].is_monorepo is False

    assert "./auth" in import_sources
    assert import_sources["./auth"].is_internal is True

    # Internal Monorepo / Path alias imports
    assert "@/components/Button" in import_sources
    assert import_sources["@/components/Button"].is_internal is True
    assert import_sources["@/components/Button"].is_monorepo is True

    assert "~/layout/AppHeader" in import_sources
    assert import_sources["~/layout/AppHeader"].is_internal is True
    assert import_sources["~/layout/AppHeader"].is_monorepo is True

    assert "@repo/core" in import_sources
    assert import_sources["@repo/core"].is_internal is True
    assert import_sources["@repo/core"].is_monorepo is True

    assert "@workspace/theme" in import_sources
    assert import_sources["@workspace/theme"].is_internal is True
    assert import_sources["@workspace/theme"].is_monorepo is True

    assert "@shared/utils" in import_sources
    assert import_sources["@shared/utils"].is_internal is True
    assert import_sources["@shared/utils"].is_monorepo is True


def test_named_default_and_reexports(parser: JavaScriptParser):
    code = """
export * from './submodule';
export * as formatters from './formatters';
export { originalA, originalB as renamedB } from './helpers';

export const API_VERSION = 'v1';
export default function mainApp() {
  return true;
}
"""
    result = parser.parse(code, "src/exports.ts")

    # Exports
    assert "*" in result.exports
    assert "formatters" in result.exports
    assert "originalA" in result.exports
    assert "renamedB" in result.exports
    assert "API_VERSION" in result.exports
    assert "default" in result.exports or "mainApp" in result.exports

    # Re-exports tracked as imports
    reexport_sources = [imp.source for imp in result.imports]
    assert "./submodule" in reexport_sources
    assert "./formatters" in reexport_sources
    assert "./helpers" in reexport_sources


def test_classes_inheritance_properties_and_methods(parser: JavaScriptParser):
    code = """
@Component({ selector: 'user-manager' })
export class UserManager<T extends User> extends BaseService implements IManager, IDisposable {
  private cache: Map<string, T> = new Map();
  public readonly version: number = 2;
  static DEFAULT_TIMEOUT = 5000;

  constructor() {
    super();
  }

  public async getUser(id: string): Promise<T | null> {
    if (this.cache.has(id)) {
      return this.cache.get(id) ?? null;
    }
    return null;
  }
}
"""
    result = parser.parse(code, "src/services/UserManager.ts")
    assert len(result.classes) == 1
    cls = result.classes[0]

    assert cls.name == "UserManager"
    assert cls.is_exported is True
    assert cls.metadata.get("extends") == "BaseService"
    assert "IManager" in cls.metadata.get("implements", [])
    assert "IDisposable" in cls.metadata.get("implements", [])
    assert "<T extends User>" in (cls.metadata.get("type_parameters") or "")

    # Decorators
    decorators = cls.metadata.get("decorators", [])
    assert "Component" in decorators

    # Properties
    props = {p["name"]: p for p in cls.metadata.get("properties", [])}
    assert "cache" in props
    assert props["cache"]["visibility"] == "private"

    assert "version" in props
    assert props["version"]["visibility"] == "public"
    assert props["version"]["is_readonly"] is True

    assert "DEFAULT_TIMEOUT" in props
    assert props["DEFAULT_TIMEOUT"]["is_static"] is True

    # Methods
    method_names = cls.metadata.get("methods", [])
    assert "getUser" in method_names
    details = {m["name"]: m for m in cls.metadata.get("method_details", [])}
    assert "getUser" in details
    assert details["getUser"]["is_async"] is True
    assert details["getUser"]["visibility"] == "public"
    assert "Promise<T | null>" in (details["getUser"]["return_type"] or "")


def test_functions_async_arrow_and_exported_constants(parser: JavaScriptParser):
    code = """
export const MAX_RETRY_COUNT = 5;
export const API_ENDPOINT: string = 'https://api.domain.com';

export async function fetchWithRetry<T>(url: string, attempts: number = 3): Promise<T> {
  let count = attempts;
  while (count > 0) {
    try {
      return await (fetch(url) as any).json();
    } catch (e) {
      count--;
    }
  }
  throw new Error('Failed');
}

export const processPayload = async (data: any, isValid: boolean): Promise<boolean> => {
  if (data && isValid) {
    return true;
  }
  return false;
};
"""
    result = parser.parse(code, "src/utils.ts")

    # Exported constants in variables
    constants = {v.name: v for v in result.variables}
    assert "MAX_RETRY_COUNT" in constants
    assert constants["MAX_RETRY_COUNT"].is_exported is True
    assert constants["MAX_RETRY_COUNT"].kind == "constant"
    assert "API_ENDPOINT" in constants

    # Functions
    fns = {f.name: f for f in result.functions}
    assert "fetchWithRetry" in fns
    fetch_fn = fns["fetchWithRetry"]
    assert fetch_fn.is_async is True
    assert fetch_fn.is_exported is True
    assert "<T>" in (fetch_fn.metadata.get("type_parameters") or "")
    assert "Promise<T>" in (fetch_fn.metadata.get("return_type") or "")
    assert fetch_fn.metadata.get("complexity", {}).get("cyclomatic", 1) >= 2

    assert "processPayload" in fns
    arrow_fn = fns["processPayload"]
    assert arrow_fn.is_async is True
    assert arrow_fn.is_exported is True
    assert arrow_fn.metadata.get("complexity", {}).get("cyclomatic", 1) >= 2


def test_modern_syntax_line_ranges_and_optional_chaining(parser: JavaScriptParser):
    code = """
interface ApiResponse<T> {
  data?: T;
  error?: { message: string; code?: number };
}

export const SafeHeader = <T,>({ response }: { response?: ApiResponse<T> }) => {
  const code = response?.error?.code ?? 200;
  return <div className="header">{code}</div>;
};
"""
    result = parser.parse(code, "src/components/SafeHeader.tsx")

    # Line ranges
    assert len(result.interfaces) == 1
    iface = result.interfaces[0]
    assert iface.line == 2
    assert iface.end_line == 5
    assert iface.metadata.get("type_parameters") == "<T>"

    # Components
    assert len(result.components) == 1
    comp = result.components[0]
    assert comp.name == "SafeHeader"
    assert comp.line == 7
    assert comp.end_line == 10

