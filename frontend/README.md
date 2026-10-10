# Frontend: evaluation dashboard

Next.js 16 (App Router) + Tailwind CSS v4 + shadcn/ui (Base UI) dashboard for the FastAPI backend.

## Run

```bash
npm install
npm run dev        # http://localhost:3000
```

The backend must be running (see `../backend`). Its URL comes from `NEXT_PUBLIC_API_URL`
(default `http://localhost:8000`); copy `.env.example` to `.env.local` to change it.

## Structure

```
src/
├── app/
│   ├── layout.tsx          theme (light/dark) + tooltip providers
│   └── page.tsx            the dashboard page: loads data, holds state
├── components/
│   ├── run-form.tsx        choose agent, dataset, evaluators → run
│   ├── run-history.tsx     list of past runs
│   ├── run-summary.tsx     report card: stat tiles, score bars, cases table
│   ├── theme-toggle.tsx    light/dark switch
│   └── ui/                 shadcn/ui components (add more: npx shadcn@latest add <name>)
└── lib/
    ├── api.ts              typed API client (types mirror backend schemas)
    └── utils.ts
```

## Scripts

| Command | Does |
|---|---|
| `npm run dev` | dev server with hot reload |
| `npm run build` / `npm start` | production build / serve it |
| `npm run lint` | ESLint |
