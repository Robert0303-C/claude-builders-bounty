# CLAUDE.md — Next.js 15 + SQLite SaaS Template

> Opinionated Claude Code context file for a typical production SaaS. Pairs with `create-next-app` and `better-sqlite3` (or Turso). Drop this into the repo root and Claude Code will follow these conventions without asking clarifying questions.

---

## Stack & versions

- **Framework**: Next.js 15 (App Router, RSC, Server Actions)
- **Language**: TypeScript 5.6+ (strict mode on)
- **Runtime**: Node 22 LTS
- **Package manager**: pnpm 9 (never npm, never yarn — see "What we don't do")
- **Database**: SQLite via `better-sqlite3` locally, Turso (libSQL) in production
- **ORM**: Drizzle ORM (not Prisma — see "What we don't do")
- **Auth**: Auth.js v5 (NextAuth successor) with email magic link
- **Billing**: Stripe (checkout + customer portal)
- **Styling**: Tailwind CSS v4 + shadcn/ui components
- **Forms**: react-hook-form + zod
- **Email**: Resend (transactional) + react-email (templates)
- **Testing**: Vitest (unit) + Playwright (e2e)
- **Linting/formatting**: Biome (not ESLint + Prettier)

## Folder structure

```
/
├── app/                    # Next.js App Router
│   ├── (marketing)/        # Public marketing pages (no auth)
│   │   ├── page.tsx
│   │   └── pricing/
│   ├── (app)/              # Authenticated app shell
│   │   ├── layout.tsx      # Checks session, redirects to /signin
│   │   ├── dashboard/
│   │   └── settings/
│   ├── (api)/              # Route handlers
│   │   ├── webhooks/
│   │   │   └── stripe/
│   │   └── trpc/           # tRPC entry (if used)
│   └── layout.tsx
├── components/
│   ├── ui/                 # shadcn primitives (don't edit, regenerate)
│   ├── forms/              # Composed form components
│   └── marketing/
├── db/
│   ├── schema.ts           # Drizzle schema
│   ├── migrations/         # Generated SQL files
│   └── client.ts           # Drizzle client + connection
├── lib/
│   ├── auth.ts             # Auth.js config
│   ├── stripe.ts           # Stripe SDK + helpers
│   ├── email.ts            # Resend client
│   └── utils.ts            # cn() + small helpers
├── emails/                 # react-email templates
├── tests/
│   ├── unit/               # Vitest specs
│   └── e2e/                # Playwright specs
├── public/
├── .env.example            # All env vars documented, no real values
├── drizzle.config.ts
├── next.config.ts
├── biome.json
├── tsconfig.json           # strict: true, noUncheckedIndexedAccess: true
├── tailwind.config.ts
└── package.json
```

## SQL / migration conventions

- **Schema lives in `db/schema.ts`** as Drizzle table definitions; never write raw SQL in app code.
- **Migrations are generated, never hand-edited**: `pnpm db:generate` → `pnpm db:migrate`.
- **Migrations are append-only** in version control. Never rewrite history, even locally. If a migration is wrong, write a forward-fix migration.
- **Every table has**: `id` (UUID, default `crypto.randomUUID()`), `created_at` (integer, unix ms), `updated_at` (integer, unix ms).
- **Soft delete by default**: add `deleted_at` (nullable integer). Hard deletes are gated behind an explicit admin tool.
- **Foreign keys always have an explicit index** (`(table) => ({ userIdx: index('user_id_idx').on(table.userId) })`).
- **Naming**: `snake_case` for columns, `camelCase` for Drizzle property names, `PascalCase` singular for table names (`user`, not `users`).
- **Money in integer cents**, never floats. Currency is a separate `currency` column, default `'USD'`.
- **Timestamps in unix ms** (integer), not ISO strings. Convert at the edge if you need to display.

## Component patterns

- **Server Components by default**. Add `"use client"` only when the component needs state, effects, or browser APIs.
- **One component per file**. File name = component name in `PascalCase`. Co-locate component-specific types in the same file.
- **Props type exported** as `interface FooProps`, not `type`. Use `type` only for unions/intersections.
- **Forms**: every form is a `react-hook-form` + `zod` schema. Inline `<form onSubmit>` is forbidden — use the `<Form />` shadcn wrapper.
- **Loading states**: every async server component has a sibling `loading.tsx` in the same folder. No raw `if (loading) return <Spinner />` in the component body.
- **Errors**: every route segment has an `error.tsx` that renders the standard error boundary. The error message goes to Sentry, not the user.
- **No CSS modules**. Tailwind utility classes only. Custom values go in `tailwind.config.ts` under `theme.extend`.
- **Icons**: `lucide-react` only. Never paste inline SVGs.

## TypeScript conventions

- **`strict: true`** and **`noUncheckedIndexedAccess: true`** in `tsconfig.json`. Never relax these.
- **No `any`**. Use `unknown` + a zod parse, or define a proper type.
- **Prefer `type` imports** for types-only: `import type { User } from '@/db/schema'`.
- **Path alias `@/`** for everything under `app/`, `components/`, `lib/`, `db/`. No `../../../` chains.
- **Throw, don't return error objects**. `throw new Error('Subscription not found')` — let the error boundary catch it.

## Dev commands

| Command | Purpose |
|---|---|
| `pnpm dev` | Start Next.js dev server on :3000 |
| `pnpm build` | Production build |
| `pnpm start` | Run production build |
| `pnpm test` | Vitest in watch mode |
| `pnpm test:run` | Vitest once |
| `pnpm test:e2e` | Playwright |
| `pnpm db:generate` | Generate a new Drizzle migration from schema changes |
| `pnpm db:migrate` | Apply pending migrations |
| `pnpm db:studio` | Open Drizzle Studio (DB GUI) |
| `pnpm lint` | Biome check + format |
| `pnpm typecheck` | `tsc --noEmit` |
| `pnpm stripe:listen` | Forward Stripe webhooks to localhost |

Always run `pnpm typecheck && pnpm lint` before committing. CI will fail otherwise.

## Patterns to follow

- **Auth check at the layout level**, not inside every page. `app/(app)/layout.tsx` calls `auth()` and redirects — pages trust the session.
- **Server Actions for mutations**, not `/api/*` POST handlers, unless the route is webhook-shaped (Stripe, GitHub, etc.).
- **Validate every input with zod**, including Server Action form data and webhook payloads. The first line of any action is `const data = schema.parse(formData)`.
- **One source of truth for env vars**: `lib/env.ts` exports a zod-parsed `env` object. Importing `process.env` directly is a lint error.
- **Stripe webhooks verify signatures**. Raw body, never JSON-parsed. See `app/(api)/webhooks/stripe/route.ts`.
- **All money math via `dinero.js`**, not raw integer math. Currency-aware arithmetic prevents rounding bugs.
- **Date math via `date-fns`**, not `moment` or hand-rolled Date arithmetic.

## Anti-patterns to avoid

- **`useEffect` for data fetching**. Use Server Components or `react-query` (TanStack Query) for client-side data.
- **Client-side auth checks in protected pages**. Always check in the layout.
- **Storing money as floats**. Cents in an integer, always.
- **Storing timestamps as ISO strings**. Unix ms in an integer, always.
- **Inline event handlers that fetch**. Use Server Actions.
- **Importing from `node_modules` directly in Server Components** without a `'server-only'` import on the wrapper.
- **Generating IDs with `Math.random()`**. Use `crypto.randomUUID()` server-side, or a deterministic slug for human-readable IDs.

## What we don't do (and why)

- **No Prisma.** Drizzle is faster, generates less runtime code, and produces plain SQL you can read.
- **No npm / yarn.** pnpm is faster, disk-efficient, and stricter about phantom dependencies.
- **No ESLint + Prettier.** Biome does both in one tool, 10× faster, and the rules are similar enough that migration is painless.
- **No Redux / Zustand for server state.** Server Components own server state. For client state that survives navigation, use URL state (`useSearchParams`) or `react-query`.
- **No CSS-in-JS.** Tailwind is fast, deterministic, and works with Server Components.
- **No `useState` for form values.** `react-hook-form` handles it with less re-rendering and built-in validation.
- **No barrel files (`index.ts` re-exports).** They break tree-shaking and slow down builds. Import directly from the source file.
- **No default exports for utilities.** Named exports only, always. Default exports only for React components and pages.
- **No `Date` in business logic.** All date math goes through `date-fns` to dodge timezone bugs.
- **No manual `JSON.parse` on request bodies.** Webhook handlers read raw bodies, then zod-parse.

## When you're stuck

1. Check if there's a shadcn component for it (`pnpm dlx shadcn@latest add <name>`).
2. Check Drizzle docs for the SQL operation (`https://orm.drizzle.team/docs/select`).
3. Check the Next.js 15 docs (`https://nextjs.org/docs/app`) — App Router is the only supported router.
4. Ask. If you're about to write 50 lines of code that feel weird, ask first. Convention beats cleverness.

## Conventions for Claude Code

- **Always run `pnpm typecheck` after edits** that touch `.ts` or `.tsx` files.
- **Always run `pnpm lint` before declaring a task done** — Biome will auto-fix what it can.
- **Never `git commit` without an explicit user instruction** to commit.
- **Never `git push` without an explicit user instruction** to push.
- **Never install a new package** without asking first. Suggest the package + why, then wait.
- **If a task is ambiguous**, ask one clarifying question with a default option. Don't ask 5.
- **When you write SQL**, prefer Drizzle query builder over raw SQL strings.
- **When you add a migration**, regenerate + apply, then commit the migration file.
- **When you write a Server Action**, return a typed result: `{ ok: true, data } | { ok: false, error: string }`. Never throw to the client.
- **When in doubt, look at an existing file in the same directory** for the pattern to follow.
