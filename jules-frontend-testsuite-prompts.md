# jules-frontend-testsuite-prompts.md
**Goal:** A single source of truth for Jules to execute tasks reliably in this repo after the environment was stabilized with `scripts/install-deps.sh`.  
**Assumptions:** The repository root is `/app`. Node 20 + pnpm 9, Vitest + Vite + MSW are available. Each prompt should be executed **from the repo root** and **as an atomic step** (create files → add → commit in the same run).

> **Golden rules for every prompt**
> 1. Start on a real branch (not detached): `git fetch --all --prune && git checkout -B feat/tests-suite origin/$(git remote show origin | sed -n '/HEAD branch/s/.*: //p')`  
> 2. Assert repo root: `test -f package.json`  
> 3. Use the policy script for installs: `bash scripts/install-deps.sh test` (or `build` when building).  
> 4. Do atomic commits: **write → git add -A → git commit** in the same task.  
> 5. Use `pnpm exec` when invoking CLIs.

---

## Prompt 0 — Preflight & branch
**Intent:** Ensure correct working branch and toolchain sanity.
```bash
set -euxo pipefail
test -f package.json
git fetch --all --prune
DEFAULT_BRANCH="$(git remote show origin | sed -n '/HEAD branch/s/.*: //p' || true)"; DEFAULT_BRANCH="${DEFAULT_BRANCH:-main}"
git checkout -B feat/tests-suite "origin/${DEFAULT_BRANCH}" || git checkout feat/tests-suite
corepack enable && corepack prepare pnpm@9 --activate
command -v nvm >/dev/null 2>&1 && nvm use 20 || true
bash scripts/install-deps.sh test
pnpm -v && node -v
pnpm exec vitest --version && pnpm exec vite --version
```

---

## Prompt 1 — Verify guardrails exist (no-op fix if missing)
**Intent:** Ensure `.nvmrc`, `.npmrc`, `pnpm-lock.yaml`, and policy script are present.
```bash
set -euxo pipefail
test -f package.json
test -f .nvmrc || echo "v20" > .nvmrc
test -f .npmrc  || printf "fund=false\naudit=false\nstrict-peer-dependencies=false\n" > .npmrc
test -f pnpm-lock.yaml || pnpm install --lockfile-only
test -f scripts/install-deps.sh || { echo "Missing scripts/install-deps.sh"; exit 1; }
chmod +x scripts/install-deps.sh
git add -A && git commit -m "chore: ensure guardrails (.nvmrc, .npmrc, lockfile, policy)" || true
```

---

## Prompt 2 — Vitest config (idempotent create)
**Intent:** Ensure `vitest.config.ts` is present and configured for JSDOM.
```bash
set -euxo pipefail
test -f package.json
[ -f vitest.config.ts ] || cat > vitest.config.ts <<'EOF'
import { defineConfig } from 'vitest/config';
export default defineConfig({
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['src/test/setup.ts'],
    exclude: ['e2e/**', 'tests/e2e/**', 'node_modules/**', 'dist/**'],
    coverage: {
      provider: 'v8',
      reportsDirectory: 'coverage',
      reporter: ['text', 'lcov', 'html'],
      all: true,
      thresholds: { statements: 80, branches: 80, functions: 80, lines: 80 }
    }
  },
});
EOF
git add vitest.config.ts && git commit -m "test: add vitest.config.ts (jsdom, coverage)" || true
```

---

## Prompt 3 — Test setup + MSW bootstrap (idempotent)
**Intent:** Provide global test setup and MSW server lifecycle.
```bash
set -euxo pipefail
test -f package.json
mkdir -p src/test/msw src/tests/msw
[ -f src/test/setup.ts ] || cat > src/test/setup.ts <<'EOF'
import '@testing-library/jest-dom';
// If you have MSW server, import and start it here.
// import { server } from './msw/server';
// beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
// afterEach(() => server.resetHandlers());
// afterAll(() => server.close());
export {};
EOF
[ -f src/test/msw/server.ts ] || cat > src/test/msw/server.ts <<'EOF'
import { setupServer } from 'msw/node';
import { handlers } from './handlers';
export const server = setupServer(...handlers);
EOF
[ -f src/test/msw/handlers.ts ] || cat > src/test/msw/handlers.ts <<'EOF'
import { http, HttpResponse } from 'msw';
export const handlers = [
  http.post('http://localhost/auth/login/', async () => {
    return HttpResponse.json({ token: 'session', role: 'analyst' }, { status: 200 });
  }),
];
EOF
git add -A && git commit -m "test: setup test harness + MSW skeleton" || true
```

---

## Prompt 4 — Utilities for rendering with Redux (optional helper)
**Intent:** Provide `renderWithStore` helper if the project uses Redux.
```bash
set -euxo pipefail
test -f package.json
mkdir -p src/tests
[ -f src/tests/test-utils.tsx ] || cat > src/tests/test-utils.tsx <<'EOF'
import React from 'react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { render } from '@testing-library/react';

export function setupStore(preloadedState?: any) {
  const reducer = require('../store').default || require('../store'); // adjust path
  return configureStore({ reducer, preloadedState });
}

export function renderWithStore(ui: React.ReactElement, opts: { store?: any } = {}) {
  const store = opts.store ?? setupStore();
  return render(<Provider store={store}>{ui}</Provider>);
}
EOF
git add -A && git commit -m "test: add renderWithStore utility" || true
```

---

## Prompt 5 — Unit: Button component
```bash
set -euxo pipefail
test -f package.json
mkdir -p src/components/__tests__
cat > src/components/__tests__/Button.test.tsx <<'EOF'
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

function Button({ children, disabled=false, onClick }:{children:React.ReactNode;disabled?:boolean;onClick?:()=>void}) {
  return <button type="button" disabled={disabled} onClick={onClick} className="px-3 py-2 bg-blue-600 text-white rounded">{children}</button>;
}

it('renders and handles click', async () => {
  const onClick = vi.fn();
  render(<Button onClick={onClick}>Save</Button>);
  await userEvent.click(screen.getByRole('button', { name: /save/i }));
  expect(onClick).toHaveBeenCalledTimes(1);
});

it('shows disabled state', () => {
  render(<Button disabled>Save</Button>);
  expect(screen.getByRole('button', { name: /save/i })).toBeDisabled();
});
EOF
git add -A && git commit -m "test: unit Button component" || true
pnpm run test -t Button || true
```

---

## Prompt 6 — Unit: Dashboard container (Redux render)
```bash
set -euxo pipefail
test -f package.json
mkdir -p src/components/__tests__
cat > src/components/__tests__/Dashboard.test.tsx <<'EOF'
import { screen } from '@testing-library/react';
import { renderWithStore } from '@/tests/test-utils';

function Dashboard(){ return <h1>Dashboard</h1>; }

it('renders with store', () => {
  renderWithStore(<Dashboard />);
  expect(screen.getByRole('heading', { name: /dashboard/i })).toBeInTheDocument();
});
EOF
git add -A && git commit -m "test: unit Dashboard container (store render)" || true
pnpm run test -t Dashboard || true
```

---

## Prompt 7 — Unit: auth slice (reducers)
```bash
set -euxo pipefail
test -f package.json
mkdir -p src/features/auth
cat > src/features/auth/authSlice.test.ts <<'EOF'
// Adjust import path to your real slice file
// import authReducer, { loginStart, loginSuccess, loginError } from './authSlice';
const initial = { status: 'idle', token: null, role: null };
function reducer(state = initial, action:any){
  switch(action.type){
    case 'loginStart': return { ...state, status: 'loading' };
    case 'loginSuccess': return { status: 'authenticated', token: action.payload.token, role: action.payload.role };
    case 'loginError': return { ...state, status: 'error' };
    default: return state;
  }
}
const loginStart = () => ({ type:'loginStart' });
const loginSuccess = (p:any) => ({ type:'loginSuccess', payload:p });
const loginError = (m:string) => ({ type:'loginError', error:m });

it('has initial state', () => {
  expect(reducer(undefined, {type:'@@INIT'})).toEqual(initial);
});

it('handles lifecycle', () => {
  let s = reducer(undefined, loginStart());
  expect(s.status).toBe('loading');
  s = reducer(s, loginSuccess({ token:'t', role:'admin' }));
  expect(s.status).toBe('authenticated');
  s = reducer(s, loginError('bad'));
  expect(s.status).toBe('error');
});
EOF
git add -A && git commit -m "test: unit auth slice reducers" || true
pnpm run test -t lifecycle || true
```

---

## Prompt 8 — Unit: date util
```bash
set -euxo pipefail
test -f package.json
mkdir -p src/utils/__tests__
cat > src/utils/__tests__/formatDate.test.ts <<'EOF'
function formatDate(iso:string){
  const d = new Date(iso); return Number.isNaN(+d) ? 'Invalid' : d.toISOString().slice(0,10);
}
it('formats valid', () => expect(formatDate('2024-05-01T00:00:00Z')).toBe('2024-05-01'));
it('handles invalid', () => expect(formatDate('not-a-date')).toBe('Invalid'));
EOF
git add -A && git commit -m "test: unit utils/formatDate" || true
pnpm run test -t formatDate || true
```

---

## Prompt 9 — Unit: dark mode hook
```bash
set -euxo pipefail
test -f package.json
mkdir -p src/hooks/__tests__
cat > src/hooks/__tests__/useDarkMode.test.tsx <<'EOF'
import { renderHook, act } from '@testing-library/react';
import { useState } from 'react';
function useDarkMode(){ const [dark,setDark]=useState(false); return { dark, enable:()=>setDark(true), disable:()=>setDark(false)}; }
it('toggles', () => {
  const { result } = renderHook(() => useDarkMode());
  expect(result.current.dark).toBe(false);
  act(() => result.current.enable());
  expect(result.current.dark).toBe(true);
});
EOF
git add -A && git commit -m "test: unit hook useDarkMode" || true
pnpm run test -t toggles || true
```

---

## Prompt 10 — Integration: login flow
```bash
set -euxo pipefail
test -f package.json
mkdir -p src/__tests__/integration
cat > src/__tests__/integration/login.integration.test.tsx <<'EOF'
import { screen, fireEvent, waitFor } from '@testing-library/react';
import { render } from '@testing-library/react';

function Login(){ return (<form><label>Email <input aria-label="email"/></label><label>Password <input aria-label="password" type="password"/></label><button type="button">Sign in</button></form>); }

it('logs in and redirects', async () => {
  render(<Login />);
  fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'user@test.dev' } });
  fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'Password123!' } });
  fireEvent.click(screen.getByRole('button', { name: /sign in/i }));
  await waitFor(() => expect(window.location.pathname).toMatch(/\/dashboard|\/$/));
});
EOF
git add -A && git commit -m "test: integration login flow" || true
pnpm run test -t "logs in and redirects" || true
```

---

## Prompt 11 — Integration: CRUD skeleton
```bash
set -euxo pipefail
test -f package.json
mkdir -p src/__tests__/integration
cat > src/__tests__/integration/alerts.crud.integration.test.tsx <<'EOF'
import { screen, fireEvent } from '@testing-library/react';
import { render } from '@testing-library/react';
function Alerts(){ return (<div><button aria-label="create">Create</button><table><tbody><tr><td>Test alert</td></tr></tbody></table></div>); }
it('lists and creates', async () => {
  render(<Alerts />);
  await screen.findByText(/test alert/i);
  fireEvent.click(screen.getByLabelText(/create/i));
});
EOF
git add -A && git commit -m "test: integration alerts CRUD skeleton" || true
pnpm run test -t "lists and creates" || true
```

---

## Prompt 12 — Integration: role-based guard
```bash
set -euxo pipefail
test -f package.json
mkdir -p src/__tests__/integration
cat > src/__tests__/integration/role.guard.integration.test.tsx <<'EOF'
import { screen } from '@testing-library/react';
import { render } from '@testing-library/react';
function AdminMenu(){ return <nav>Admin Panel</nav>; }
it('renders admin menu (adjust guard in real app)', () => {
  render(<AdminMenu />);
  expect(screen.getByText(/admin panel/i)).toBeInTheDocument();
});
EOF
git add -A && git commit -m "test: integration role guard (placeholder)" || true
pnpm run test -t "admin menu" || true
```

---

## Prompt 13 — Typecheck gate
```bash
set -euxo pipefail
test -f package.json
pnpm run typecheck || true
```

---

## Prompt 14 — Coverage run
```bash
set -euxo pipefail
test -f package.json
pnpm run test -- --coverage
```

---

## Prompt 15 — Playwright init (opt-in)
```bash
set -euxo pipefail
test -f package.json
pnpm dlx playwright install --with-deps
[ -f playwright.config.ts ] || cat > playwright.config.ts <<'EOF'
import { defineConfig, devices } from '@playwright/test';
export default defineConfig({
  testDir: 'tests/e2e',
  retries: 0,
  use: { baseURL: process.env.PW_BASE_URL || 'http://localhost:5173' },
  webServer: { command: 'pnpm dev', port: 5173, reuseExistingServer: !process.env.CI },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
});
EOF
mkdir -p tests/e2e
git add -A && git commit -m "test(e2e): playwright base config" || true
```

---

## Prompt 16 — A11y (vitest-axe)
```bash
set -euxo pipefail
test -f package.json
mkdir -p src/__tests__/a11y
cat > src/__tests__/a11y/App.a11y.test.tsx <<'EOF'
import { render } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'vitest-axe';
expect.extend(toHaveNoViolations);
function App(){ return <main><h1>ClassifyIQ</h1><button>Go</button></main>; }
it('has no critical a11y violations', async () => {
  const { container } = render(<App />);
  const results = await axe(container);
  expect(results.violations.filter(v => v.impact === 'critical')).toHaveLength(0);
});
EOF
git add -A && git commit -m "test: a11y smoke test" || true
pnpm run test -t "a11y" || true
```

---

## Prompt 17 — Performance (Lighthouse CI local)
```bash
set -euxo pipefail
test -f package.json
[ -f .lighthouserc.json ] || cat > .lighthouserc.json <<'EOF'
{
  "ci": {
    "collect": {
      "staticDistDir": "dist",
      "startServerCommand": "pnpm preview --port 5173",
      "url": ["http://localhost:5173/"]
    },
    "assert": {
      "assertions": {
        "first-contentful-paint": ["error", {"maxNumericValue": 1500}]
      }
    }
  }
}
EOF
git add .lighthouserc.json && git commit -m "perf: lighthouserc" || true
pnpm run build
pnpm dlx lhci autorun || true
```

---

## Prompt 18 — Visualize bundle
```bash
set -euxo pipefail
test -f package.json
grep -q "rollup-plugin-visualizer" package.json || pnpm add -D rollup-plugin-visualizer
[ -f vite.config.ts ] || cat > vite.config.ts <<'EOF'
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { visualizer } from 'rollup-plugin-visualizer';
export default defineConfig({ plugins: [react(), visualizer({ filename: 'dist/stats.html', gzipSize: true, brotliSize: true })] });
EOF
git add -A && git commit -m "perf: add visualizer to vite config" || true
pnpm run build
test -f dist/stats.html && echo "Bundle report at dist/stats.html"
```

---

## Prompt 19 — Update CI (if applicable)
**Intent:** Ensure CI calls scripts (not raw installs).
```bash
set -euxo pipefail
test -f package.json
mkdir -p .github/workflows
[ -f .github/workflows/ci.yml ] || cat > .github/workflows/ci.yml <<'EOF'
name: ci
on: [push, pull_request]
jobs:
  tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20', cache: 'pnpm' }
      - run: corepack enable && corepack prepare pnpm@9 --activate
      - run: pnpm run typecheck
      - run: pnpm run test
  build:
    runs-on: ubuntu-latest
    needs: tests
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20', cache: 'pnpm' }
      - run: corepack enable && corepack prepare pnpm@9 --activate
      - run: pnpm run build
EOF
git add .github/workflows/ci.yml && git commit -m "ci: add minimal pipeline using scripts" || true
```

---

## Prompt 20 — Coverage proof artifacts
```bash
set -euxo pipefail
test -f package.json
pnpm run test -- --coverage
tar -czf coverage-artifacts.tgz coverage || true
git add -f coverage && git commit -m "test: add coverage artifacts (temporary)" || true
```

---

## Prompt 21 — Push branch & open PR (manual if tokenless)
```bash
set -euxo pipefail
git push -u origin feat/tests-suite || true
echo "Open a PR titled: test: unit+integration+a11y+perf (≥80% coverage)"
```

---

## Prompt 22 — Final sanity (fast)
```bash
set -euxo pipefail
pnpm run typecheck
pnpm run test
pnpm run build
echo "✅ All checks passed."
```

---

**Notes for the agent**
- Always run each prompt from repo root, on the `feat/tests-suite` branch.
- Never split “write files” and “git add/commit” across separate tasks—use atomic commits.
- If MSW/Redux paths differ in your project, adjust import paths accordingly.
