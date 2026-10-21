# Contributing to CodeAtlas

Thank you for your interest in contributing to CodeAtlas. This document provides guidelines and standards for contributing features, bug fixes, documentation, and infrastructure enhancements.

---

## Development Standards & Tooling

### Prerequisites
- **Node.js**: >= 20.0.0
- **pnpm**: >= 9.0.0
- **Python**: >= 3.11
- **Docker & Docker Compose**: For PostgreSQL (pgvector), Redis, MinIO, and Ollama

### Environment Initialization

```bash
# Clone repository
git clone https://github.com/Inkesk-Dozing/CodeAtlas.git
cd CodeAtlas

# Install dependencies
pnpm install

# Setup local environment
cp .env.example .env

# Start infrastructure containers
docker compose -f infra/docker-compose.yml up -d

# Run database migrations
pnpm db:migrate

# Start development servers
pnpm dev
```

---

## Commit Message Conventions

CodeAtlas strictly enforces [Conventional Commits](https://www.conventionalcommits.org/). All commit messages must follow this structure:

```
<type>(<scope>): <short summary>

[optional body]

[optional footer(s)]
```

### Allowed Types
- `feat`: A new feature implementation
- `fix`: A bug fix
- `docs`: Documentation changes only
- `style`: Code style changes (formatting, missing semi-colons, etc.)
- `refactor`: Code restructuring without functional changes
- `perf`: Performance improvements
- `test`: Adding or updating unit/integration/E2E tests
- `chore`: Maintenance, build scripts, configuration changes

### Examples
- `feat(ingestion): add tree-sitter Python AST parser engine`
- `fix(api): resolve async connection pool exhaustion on batch graph insert`
- `docs(api): update OpenAPI spec for graph neighborhood endpoint`

---

## Pull Request Process

1. **Branch Naming**: Use the pattern `<type>/<issue-number>-<short-description>` (e.g., `feat/42-tree-sitter-parser` or `fix/108-jwt-expiry`).
2. **Issue Linking**: Every Pull Request must link to an existing GitHub issue using `Closes #<issue-id>` or `Fixes #<issue-id>`.
3. **Linting & Formatting**: Ensure code adheres to Prettier, ESLint, and Ruff formatting rules before committing:
   ```bash
   pnpm format:check
   pnpm lint
   ```
4. **Unit & Integration Testing**: All pull requests must pass unit and integration tests with zero regression:
   ```bash
   pnpm test
   ```
5. **Code Review Criteria**: Pull requests require at least one approving review from a core maintainer and green CI build checks.

---

## Pre-Commit Hooks & Quality Gates

CodeAtlas utilizes pre-commit hooks to safeguard codebase integrity:
- **Secret Scanning**: Scans for hardcoded credentials via TruffleHog.
- **Code Linting & Formatting**: Enforces ESLint and Ruff compliance.
- **Type checking**: Runs `pnpm typecheck` across monorepo packages.
