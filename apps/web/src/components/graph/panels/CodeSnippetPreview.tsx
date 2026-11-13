import React from 'react';

export interface CodeSnippetPreviewProps {
  code: string;
  language?: string | null;
  startLine?: number;
  className?: string;
}

// Lightweight syntax highlighting token patterns for clean dark theme rendering
const KEYWORDS = new Set([
  'import', 'export', 'from', 'default', 'return', 'function', 'const', 'let', 'var',
  'class', 'extends', 'implements', 'interface', 'type', 'async', 'await', 'def', 'class',
  'if', 'else', 'elif', 'for', 'while', 'in', 'try', 'except', 'finally', 'raise', 'throw',
  'new', 'this', 'self', 'public', 'private', 'protected', 'static', 'readonly', 'as',
]);

const BUILTINS = new Set([
  'true', 'false', 'null', 'undefined', 'None', 'True', 'False', 'boolean', 'string',
  'number', 'any', 'void', 'int', 'str', 'float', 'list', 'dict', 'set', 'tuple', 'Promise',
]);

function highlightToken(token: string, key: number): React.ReactNode {
  if (KEYWORDS.has(token)) {
    return <span key={key} className="text-purple-400 font-semibold">{token}</span>;
  }
  if (BUILTINS.has(token)) {
    return <span key={key} className="text-amber-400">{token}</span>;
  }
  if (/^\d+(\.\d+)?$/.test(token)) {
    return <span key={key} className="text-emerald-400">{token}</span>;
  }
  if (/^["'].*["']$/.test(token)) {
    return <span key={key} className="text-emerald-300">{token}</span>;
  }
  if (/^[A-Z][a-zA-Z0-9_]*$/.test(token)) {
    return <span key={key} className="text-cyan-300 font-medium">{token}</span>;
  }
  return <span key={key}>{token}</span>;
}

function highlightLine(line: string): React.ReactNode[] {
  // Simple regex tokenizer splitting on comments, strings, identifiers, and symbols
  const parts: React.ReactNode[] = [];
  
  // Check for whole line or inline comments
  const commentIdx = line.indexOf('//') !== -1 ? line.indexOf('//') : line.indexOf('#');
  let codePart = line;
  let commentPart = '';
  
  if (commentIdx !== -1) {
    codePart = line.slice(0, commentIdx);
    commentPart = line.slice(commentIdx);
  }

  // Tokenize codePart
  const tokens = codePart.split(/([a-zA-Z_][a-zA-Z0-9_]*|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|\d+(?:\.\d+)?|\s+|[^\s\w])/);

  tokens.forEach((t, i) => {
    if (!t) return;
    parts.push(highlightToken(t, i));
  });

  if (commentPart) {
    parts.push(
      <span key="comment" className="text-muted-foreground/60 italic">
        {commentPart}
      </span>,
    );
  }

  return parts;
}

export function CodeSnippetPreview({
  code,
  startLine = 1,
  className = '',
}: CodeSnippetPreviewProps) {
  const lines = code.split('\n');

  return (
    <div
      className={`rounded-lg border border-border/80 bg-zinc-950/90 font-mono text-xs overflow-x-auto shadow-inner ${className}`}
      data-testid="code-snippet-preview"
    >
      <div className="flex divide-x divide-border/30">
        {/* Line numbers column */}
        <div className="select-none py-2 px-3 text-right text-muted-foreground/40 bg-zinc-900/40">
          {lines.map((_, idx) => (
            <div key={idx} className="leading-5">
              {startLine + idx}
            </div>
          ))}
        </div>

        {/* Code lines column */}
        <div className="py-2 px-3.5 flex-1 whitespace-pre leading-5 text-zinc-200">
          {lines.map((line, idx) => (
            <div key={idx} className="leading-5 hover:bg-zinc-800/40 px-1 -mx-1 rounded">
              {highlightLine(line)}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
