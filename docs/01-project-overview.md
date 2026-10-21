# CodeAtlas - Project Overview

## Vision
An AI-augmented monorepo onboarding engine that reduces developer onboarding time from weeks to hours by automatically mapping and explaining complex codebases through interactive visual graphs.

## Core Problem
- Documentation goes stale instantly in fast-moving codebases
- New developers spend weeks understanding architecture before contributing
- No automated way to map issues to affected code areas
- Monorepos (Turborepo/pnpm) add complexity with shared packages and interdependencies

## Solution
CodeAtlas connects to GitHub, analyzes repository structure, and generates:
1. **Interactive Architecture Graph** - Node-based visualization of modules, services, and dependencies
2. **Issue-to-Code Mapping** - Highlights exact files/routes/models/components affected by a GitHub Issue
3. **Natural Language Query** - "Where is auth middleware?" → precise file locations with context
4. **Auto-Generated Documentation** - Living docs that update with every commit

## Target Users
- Engineering teams onboarding new hires
- Student coding clubs / open source contributors
- Platform teams managing large monorepos
- Consultants auditing unfamiliar codebases

## Success Metrics
- Onboarding time reduction: 80%+ (weeks → hours)
- Issue resolution time reduction: 40%+
- Developer satisfaction score: 4.5/5+
- Adoption: 100+ active repositories within 6 months