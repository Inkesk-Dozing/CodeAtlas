## 📌 Description

Please include a concise summary of the changes, relevant context, and why this pull request is needed.

Fixes / Closes #[Issue Number]

---

## 🛠️ Type of Change

- [ ] `feat`: New feature (non-breaking change adding functionality)
- [ ] `fix`: Bug fix (non-breaking change fixing an issue)
- [ ] `perf`: Performance optimization
- [ ] `refactor`: Code change that neither fixes a bug nor adds a feature
- [ ] `docs`: Documentation updates
- [ ] `test`: Unit, integration, or E2E test additions
- [ ] `chore`: Repository maintenance or tooling update
- [ ] ⚠️ **BREAKING CHANGE**: Fix or feature that breaks backwards compatibility

---

## 📐 Scope of Changes

- [ ] `apps/api`: FastAPI backend, Celery workers, Alembic migrations
- [ ] `apps/web`: Next.js frontend, React Flow canvas, Zustand stores
- [ ] `packages/shared`: Shared TypeScript types, utilities, constants
- [ ] `infra`: Docker Compose, MinIO, PostgreSQL/pgvector, Redis
- [ ] `docs`: Architectural docs, OpenAPI specs, components
- [ ] `.github`: CI/CD workflows, issue/PR templates

---

## 🧪 Verification & Testing Matrix

### Automated Tests Executed
- [ ] `pnpm lint` passed with zero warnings
- [ ] `pnpm typecheck` passed cleanly across monorepo
- [ ] `pnpm test` unit & integration suites passed
- [ ] Python test suite (`pytest apps/api/tests`) passed with 90%+ coverage

### Manual Test Steps
1. 
2. 
3. 

---

## 🔒 Security Checklist

- [ ] No hardcoded secrets, passwords, or API keys (`TruffleHog` check passed)
- [ ] Input parameter validation enforced (`Pydantic` / `Zod`)
- [ ] Database queries use parametrized ORM statements (No raw SQL injection vector)
- [ ] Auth & RLS policies verified for multi-tenant isolation

---

## 📸 Screenshots / Visual Demos (if applicable)

*Add screenshots or GIFs illustrating UI updates or graph canvas interactions.*
