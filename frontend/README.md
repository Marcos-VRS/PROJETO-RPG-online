# Roll3d6 — Frontend (SPA + Tauri)

SPA da V2: React + Vite + TypeScript + Tailwind + axios + TanStack Query.
Empacotada como app desktop via Tauri 2.

## Setup local (após F-0 estar feita)

```bash
cd frontend
pnpm install
cp .env.example .env.local
pnpm dev
```

Aceitação:
- http://localhost:5173 carrega.
- Se não logado, mostra "Entrar" -> link para `/accounts/login/` do Django.
- Após login no Django, voltar pra `:5173` mostra "Olá, {username}!".

## Build de produção web

```bash
pnpm build
```

Saída em `dist/`.

## Build Tauri (desktop)

Requer Rust toolchain (cargo) e ferramentas nativas do SO. Ver `docs/PLATFORM_V2_EXECUTION_PLAN.md` F-3.

```bash
pnpm tauri dev      # dev com hot reload
pnpm tauri build    # binários em src-tauri/target/release/bundle/
```

## Estrutura

```
frontend/
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
├── postcss.config.js
├── .env.example
└── src/
    ├── main.tsx        # entry, providers
    ├── App.tsx         # root component
    ├── index.css       # tailwind
    ├── vite-env.d.ts   # tipos do Vite
    └── lib/
        └── api.ts      # cliente axios + helpers
```

`src-tauri/` é gerado na F-3 via `pnpm dlx @tauri-apps/cli init`.
