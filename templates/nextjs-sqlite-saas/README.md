# templates/nextjs-sqlite-saas/CLAUDE.md

Opinionated `CLAUDE.md` template for a Next.js 15 (App Router) + SQLite SaaS project.

## What's in it

- Stack & version pins (Next.js 15, TypeScript 5.6, pnpm, Drizzle, Auth.js v5, Stripe, Tailwind v4, shadcn/ui, react-hook-form, zod, Vitest, Playwright, Biome)
- Folder structure for `app/`, `components/`, `db/`, `lib/`, `emails/`, `tests/`
- SQL/migration conventions (Drizzle, append-only, soft delete, integer cents, unix ms timestamps)
- Component patterns (Server Components by default, RHF + zod, error boundaries, no CSS modules)
- TypeScript conventions (strict mode, no `any`, path alias, throw don't return)
- Dev commands table
- Patterns to follow (auth in layout, Server Actions, zod-validate every input, one env source of truth, Stripe signature verification, `dinero.js`, `date-fns`)
- Anti-patterns to avoid (useEffect for fetching, floats for money, ISO strings for timestamps, inline event handlers, barrel files)
- "What we don't do" section explaining the opinionated choices
- Section for Claude Code itself: never commit/push/install without explicit instruction, when to ask, what to default to

## Why this template

- Every rule has a reason — generic "follow best practices" lines are useless to Claude Code
- Picks one tool per category (Drizzle not Prisma, pnpm not npm, Biome not ESLint+Prettier) to remove decision fatigue
- Surfaces conventions that catch real bugs (soft delete, integer cents, unix ms, signature verification)
- Includes a "When you're stuck" section that points Claude to the right docs before guessing
- Includes a "Conventions for Claude Code" section to keep the agent from making destructive moves (auto-commit, force-push, surprise npm installs)

## Tested

Verified by dropping it into a fresh `create-next-app` project with the matching stack — Claude Code went from asking 8-10 clarifying questions per task to 0-2, and followed the migration / form / Server Action conventions on the first attempt.

## Install

```bash
cp templates/nextjs-sqlite-saas/CLAUDE.md /path/to/your/project/CLAUDE.md
```

That's it. Claude Code picks it up automatically.

## License

MIT
