# Frontend: evaluation dashboard

Next.js 16 (App Router) + Tailwind CSS v4 + shadcn/ui (Base UI) dashboard for the FastAPI backend.

## Run

```bash
npm install
npm run dev        # http://localhost:3000
```

The backend must be running (see `../backend`). Its URL comes from `NEXT_PUBLIC_API_URL`
(default `http://localhost:8000`); copy `.env.example` to `.env.local` to change it.

## Pages

| Route | Page |
|---|---|
| `/` | Home: animated hero, live stats, shortcuts, latest runs |
| `/ask` | Ask one agent one question; optional checks (expected answer, expected tools, AI judge with grading rules); save the question to a dataset |
| `/evaluate` | Run an agent over a dataset; opens the report card when done |
| `/runs` | All past runs, filterable, with delete |
| `/runs/[id]` | One run's report card, with delete |

## Structure

```
src/
├── app/
│   ├── layout.tsx            nav bar + providers (theme, tooltips, reduced-motion)
│   ├── template.tsx          page-transition animation (Framer Motion)
│   ├── page.tsx              /
│   ├── ask/ evaluate/ runs/  one folder per route; runs/[id] is the report page
├── components/
│   ├── site-nav.tsx          navigation bar (animated active pill, mobile menu, API status)
│   ├── views/                the client-side content of each page
│   ├── ask-panel.tsx         question form, result, checks, save-to-dataset
│   ├── run-form.tsx · run-summary.tsx · runs-list.tsx · delete-run-button.tsx
│   ├── reactbits/            vendored React Bits components (BlurText, CountUp, ShinyText, SpotlightCard)
│   ├── themed.tsx            React Bits wrappers that follow light/dark mode
│   └── ui/                   shadcn/ui components (add more: npx shadcn@latest add <name>)
└── lib/api.ts                typed API client (types mirror backend schemas)
```

Animations use [Motion](https://motion.dev) (Framer Motion, imported from `motion/react`) and respect the
operating system's "reduce motion" setting. React Bits components were added with
`npx shadcn@latest add https://reactbits.dev/r/<Name>-TS-TW.json`.

## Scripts

| Command | Does |
|---|---|
| `npm run dev` | dev server with hot reload |
| `npm run build` / `npm start` | production build / serve it |
| `npm run lint` | ESLint |
