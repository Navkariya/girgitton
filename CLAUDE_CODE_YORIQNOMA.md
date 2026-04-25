# 🤖 CLAUDE CODE — TO'LIQ YO'RIQNOMA
### Agentlar bilan ishlash bo'yicha optimal qo'llanma

> **Manbalar:** Rasmiy Claude Code hujjatlari (code.claude.com) · AGENTS.md standarti (agents.md) · Builder.io video (AGENTS.md amaliy qo'llanmasi) · GitHub Copilot Custom Instructions video · VS Code Agent Skills video · Eng yaxshi amaliyotlar to'plami (2025–2026)

---

## 📋 MUNDARIJA

1. [Claude Code nima?](#1-claude-code-nima)
2. [O'rnatish va sozlash](#2-ornatish-va-sozlash)
3. [CLAUDE.md — Asosiy konfiguratsiya fayli](#3-claudemd--asosiy-konfiguratsiya-fayli)
4. [AGENTS.md — Universal standart](#4-agentsmd--universal-standart)
5. [AGENTS.md — Amaliy qo'llanma (Builder.io usuli)](#5-agentsmd--amaliy-qollanma-builderio-usuli)
6. [Kontekst boshqaruvi — Eng muhim cheklov](#6-kontekst-boshqaruvi--eng-muhim-cheklov)
7. [Agentlar (Sub-agents)](#7-agentlar-sub-agents)
8. [Skills — Ko'nikmalar tizimi](#8-skills--konimalar-tizimi)
9. [VS Code Agent Skills — To'liq qo'llanma](#9-vs-code-agent-skills--toliq-qollanma)
10. [GitHub Copilot Custom Instructions](#10-github-copilot-custom-instructions)
11. [Hooks — Avtomatik ishga tushuvchi skriptlar](#11-hooks--avtomatik-ishga-tushuvchi-skriptlar)
12. [MCP Serverlar](#12-mcp-serverlar)
13. [Slash Commands — Maxsus buyruqlar](#13-slash-commands--maxsus-buyruqlar)
14. [Ish jarayoni va optimal workflow](#14-ish-jarayoni-va-optimal-workflow)
15. [Parallel sessiyalar va avtomatlashtirish](#15-parallel-sessiyalar-va-avtomatlashtirish)
16. [Xavfsizlik va ruxsatlar](#16-xavfsizlik-va-ruxsatlar)
17. [Xatolardan qochish](#17-xatolardan-qochish)
18. [Model tanlash strategiyasi](#18-model-tanlash-strategiyasi)
19. [Tayyor shablonlar](#19-tayyor-shablonlar)

---

## 1. Claude Code nima?

Claude Code — bu oddiy chatbot emas, **agentic coding muhiti**. U:

- Fayllarni o'qiydi va yozadi
- Terminalda buyruqlar ishlatadi
- Mustaqil muammolarni hal qiladi
- Siz tomosha qilayotganda yoki ketganingizda ishlaydi

**Farqi:** Siz kodni o'zingiz yozib, Claude'dan ko'rib chiqishni so'rashingiz o'rniga — nimani xohlashingizni aytasiz va Claude qanday qilib yaratishni o'zi aniqlaydi.

**Asosiy cheklov:** Claude'ning kontekst oynasi (context window) tez to'lib ketadi — va to'lgan sari sifat pasayadi. Barcha eng yaxshi amaliyotlar shu cheklovga asoslanadi.

---

## 2. O'rnatish va sozlash

```bash
# O'rnatish (Node.js kerak)
npm install -g @anthropic-ai/claude-code

# Yangilash
npm update -g @anthropic-ai/claude-code

# Ishga tushirish
claude

# Yangi loyiha uchun CLAUDE.md yaratish
claude /init
```

### Asosiy CLI buyruqlari

| Buyruq | Tavsif |
|--------|---------|
| `claude` | Interaktiv rejimni ishga tushirish |
| `claude -p "prompt"` | Bitta savol (non-interactive) |
| `claude --continue` | Oxirgi suhbatni davom ettirish |
| `claude --resume` | Suhbatlar ro'yxatidan tanlash |
| `claude /clear` | Kontekstni tozalash |
| `claude /compact` | Suhbatni qisqartirish |
| `claude /rewind` | Oldingi holatga qaytish |
| `claude /plan` | Rejalashtirish rejimi |
| `claude /hooks` | Hooks sozlamalarini ko'rish |
| `claude /permissions` | Ruxsatlarni boshqarish |
| `claude /plugin` | Plaginlar bozorini ochish |

---

## 3. CLAUDE.md — Asosiy konfiguratsiya fayli

`CLAUDE.md` — Claude har bir sessiyada **avtomatik o'qiydigan** maxsus fayl. Bu faylga proyekt haqida barqaror, muhim ma'lumotlarni yozasiz.

### Fayl joylashuvi

```
~/.claude/CLAUDE.md          # Barcha proyektlarga qo'llanadi (global)
./CLAUDE.md                  # Proyekt ildizida (git-ga qo'shiladi)
./CLAUDE.local.md            # Shaxsiy sozlamalar (.gitignore-ga qo'shing)
./src/CLAUDE.md              # Papkaga xos yo'riqnomalar
```

### CLAUDE.md formati (namunaviy)

```markdown
# Loyiha: [Loyiha nomi]

## Texnologiyalar
- Node.js 20+, TypeScript (strict mode)
- PostgreSQL 15, Redis
- Testlar: Jest, Playwright

## Muhim buyruqlar
- O'rnatish: `pnpm install`
- Dev server: `pnpm dev`
- Testlar: `pnpm test`
- Linting: `pnpm lint`
- Build: `pnpm build`

## Kod uslubi
- ES modules (import/export), CommonJS emas
- Single quotes, semicolonsiz
- Funksional yondashuv, mumkin bo'lganda

## Qoida: Testlash
- Har bir o'zgartishdan keyin testlarni ishga tushir
- Butun test to'plamini emas, alohida testlarni ishga tushir

## Muhim cheklovlar
- Hech qachon sirlarni (API keys, passwords) koda yozma
- Migratsiyalar papkasiga to'g'ridan-to'g'ri yozma
- PR yaratishdan oldin `pnpm lint && pnpm test` ni bajar

## Git workflow
- Branch nomlash: `feature/`, `fix/`, `chore/`
- PR sarlavhasi: `[modul] Tavsif`
```

### CLAUDE.md — Qoidalar

**✅ Nimani yozing:**
- Claude o'zi topa olmaydigan bash buyruqlari
- Standartdan farq qiluvchi kod uslubi
- Test yo'riqnomalari
- Repository tartibi (branch nomlash, PR qoidalari)
- Muhim arxitektura qarorlari
- Muhit o'zgaruvchilari va xususiy sozlamalar

**❌ Nimani yozmang:**
- Claude kodni o'qib o'zi biladigan narsalar
- Standart dasturlash qoidalari
- Tez-tez o'zgaradigan ma'lumotlar
- Uzun tushuntirishlar yoki qo'llanmalar
- Har bir fayl tavsifi
- "Toza kod yozing" kabi o'z-o'zidan tushunarli qoidalar

### Muhim qoidalar

> **150–200 ta yo'riqnomadan ko'p bo'lmasin** — frontier LLM'lar taxminan shuncha ko'rsatmaga mos ravishda ishlaydi. Undan ko'p bo'lsa — Claude muhim qoidalarni e'tiborsiz qoldira boshlaydi.

> **200 qatordan oshirmang** — agar CLAUDE.md juda uzun bo'lsa, Claude yarim qoidani e'tiborsiz qoldiradi.

> **Har bir satrga savol bering:** "Buni o'chirsam, Claude xato qiladimi?" — Yo'q bo'lsa, o'chirish.

### Import sintaksisi

```markdown
# CLAUDE.md
See @README.md for project overview and @package.json for available npm commands.

## Additional Instructions
- Git workflow: @docs/git-instructions.md
- API conventions: @docs/api-conventions.md
```

### Ishga tushirish buyrug'i

```bash
# CLAUDE.md ni avtomatik yaratish
claude /init
```

---

## 4. AGENTS.md — Universal standart

`AGENTS.md` — bu **barcha AI coding agentlar** uchun ochiq standart fayl. 2025-yilda Linux Foundation qoshidagi Agentic AI Foundation (AAIF) tomonidan rasmiy standart sifatida qabul qilingan.

### AGENTS.md va CLAUDE.md farqi

| Xususiyat | AGENTS.md | CLAUDE.md |
|-----------|-----------|-----------|
| Qo'llanish | Ko'p AI asboblar | Faqat Claude Code |
| Qo'llab-quvvatlash | 20+ agent (Codex, Cursor, Gemini CLI, va boshq.) | 1 asbob (ammo chuqur optimallashtirilgan) |
| GitHub-dagi foydalanish | 60,000+ repo | Keng tarqalgan |
| Maqsad | Universal standartlashtirish | Claude-ga maxsus workflow |

### Qaysi biri kerak?

```
Ko'p AI asboblar ishlatilsa → AGENTS.md asosiy, CLAUDE.md qo'shimcha
Faqat Claude Code → CLAUDE.md asosiy, AGENTS.md zaxira
Eng yaxshi yondashuv → Ikkisini ham saqlang
```

### AGENTS.md tuzilmasi (namuna)

```markdown
# AGENTS.md

## Muhit sozlamalari
- Paketlar: `pnpm install`
- Dev server: `pnpm dev`
- Testlar: `pnpm test`

## Kod uslubi
- TypeScript strict mode
- Single quotes, semicolonsiz
- Mumkin bo'lganda funksional yondashuv

## Testlash ko'rsatmalari
- CI rejasi: `.github/workflows/` da
- Testlash: `pnpm turbo run test --filter <project_name>`
- Bitta testni ishga tushirish: `pnpm vitest run -t "<test nomi>"`
- Fayl ko'chirilgandan keyin: `pnpm lint --filter <project_name>`

## PR ko'rsatmalari
- Sarlavha formati: `[loyiha_nomi] Tavsif`
- Commitdan oldin: `pnpm lint && pnpm test`
```

### Monorepo uchun ko'p AGENTS.md

```
loyiha/
├── AGENTS.md               ← Yuqori darajadagi qoidalar
├── packages/
│   ├── frontend/
│   │   └── AGENTS.md       ← Frontend-ga maxsus
│   ├── backend/
│   │   └── AGENTS.md       ← Backend-ga maxsus
│   └── devops/
│       └── AGENTS.md       ← DevOps-ga maxsus
```

> **Qoida:** Eng yaqin AGENTS.md ustunlik qiladi. Foydalanuvchi chat ko'rsatmasi hamma narsadan ustun.

---

## 5. AGENTS.md — Amaliy qo'llanma (Builder.io usuli)

> **Manba:** Builder.io tomonidan Figma→kod konvertatsiyasi bo'yicha amaliy video

Bu bo'lim AGENTS.md faylini **haqiqatan samarali** qilish uchun nozik, ammo katta farq yaratadigan usullarni ko'rsatadi. Faqat texnologiyalar ro'yxati yetarli emas — agentga aniq "do/don't" qoidalar, fayl yo'llari va yaxshi/yomon namunalar kerak.

### Muammo: Agentsiz natija nimaga o'xshaydi?

Figma dizaynini koda aylantirish so'rovini bering — agent katta codebase uchun har safar noldan boshlab ish olib boradi. Natija ko'rinishda yaxshi bo'lishi mumkin, lekin ichki muammolar bo'ladi:

```
❌ Emotion CSS noto'g'ri formatda ishlatiladi
❌ State uchun MobX o'rniga React state ishlatiladi
❌ Tooltip uchun murakkab HTML string override yaratadi
❌ Material UI'ning noto'g'ri versiyasi deb taxmin qiladi
❌ Dark mode da dizayn tokenlar o'tkazib yuboriladi
```

36 satr AGENTS.md — shu muammolarning barchasini hal qiladi.

### AGENTS.md — Do va Don't tuzilmasi

Eng oddiy va samarali yondashuv: **nima qilish** va **nima qilmaslik** ro'yxati.

```markdown
# AGENTS.md

## ✅ DO — Qiling
- MUI v5 ishlating (v3 emas!)
- Emotion CSS `styled()` formatida ishlating: `const Box = styled('div')(...)`
- State uchun MobX ishlating
- Dizayn tokenlarini ishlating (hardcoded ranglar emas)
- Grafiklar uchun ApexCharts ishlating
- Komponent out-of-the-box imkoniyatlarini ishlating (override emas)

## ❌ DON'T — Qilmang
- Ranglarni hardcode qilmang (`#FF0000` o'rniga token ishlating)
- HTML tooltip override yaratmang — kutubxona defaults'ni ishlating
- `<div>` ishlatmang — bizda tayyor komponentlar bor
- Class components ishlatmang
```

### Fayl tekshirish buyruqlari (juda muhim!)

Agent butun loyihani build qilishga urinmasligi uchun — faqat o'zgartirgan faylni tekshirsin:

```markdown
## Fayl tekshirish buyruqlari
Mumkin bo'lganda alohida fayl tekshirish buyruqlaridan foydalaning:

# Bitta faylni tekshirish
- Prettier: `npx prettier --check <file_path>`
- TypeScript: `npx tsc --noEmit <file_path>`  
- ESLint: `npx eslint <file_path>`

# To'liq build (faqat kerak bo'lganda)
- `yarn build app`
- Natijada "build muvaffaqiyatli o'tgunicha tuzat" deb ayting
```

> **Nima uchun?** Agent yangilagan fayl yo'lini biladi. Butun loyihani build qilish — vaqt va kontekst isrof.

### Loyiha tuzilmasini ko'rsatish

Agent har sessiyada qayta izlab topmasligi uchun asosiy fayllar ko'rsatiladi. Agent o'zi fayl qidira oladi, shuning uchun to'liq yo'l shart emas:

```markdown
## Loyiha tuzilmasi
- Route'lar uchun: `app.tsx` ni ko'ring
- Sidebar uchun: `app-sidebar` ni ko'ring (nomiga qarab qidiradi)
- Komponentlar asosan: `app/components/` da
- State management: `app/stores/` da
- Dizayn tokenlar: `src/theme/tokens.ts` da
- API integratsiyalar: `src/api/` da
```

### Yaxshi va yomon namuna ko'rsatish

Bu eng kuchli usul. Kodebase'da eski va yangi pattern'lar aralash bo'lsa — qaysi birini ishlatish kerakligini aniq ko'rsating:

```markdown
## Kod namunalari

### ✅ Yaxshi namunalar (shu pattern'larni ishlating)
- Funksional komponentlar: `projects.tsx`
- Form pattern: `user-settings-form.tsx`
- Dashboard pattern: `analytics-dashboard.tsx`
- MobX store: `user-store.ts`

### ❌ Yomon namunalar (bu pattern'lardan qaching)
- Class-based komponent: `get-admin.tsx` — ISHLATMANG
- Inline CSS: `legacy-widget.tsx` — ISHLATMANG
```

### API hujjatlariga ko'rsatish

Agent yangi dashboard hook qilayotganda avtomatik to'g'ri API so'rovlarini yozishi uchun:

```markdown
## API hujjatlari
- Asosiy API: `docs/api-reference.md` ni ko'ring
- Endpoint'lar: `src/api/endpoints.ts` da
- Mock data: `src/mocks/` da
- Autentifikatsiya: JWT, `Authorization: Bearer <token>` formatida
```

### Real natija taqqoslash

| | AGENTS.md siz | AGENTS.md bilan |
|---|---|---|
| Codebase exploration | Har sessiyada qayta | Yo'l ma'lum — tez |
| CSS formati | Tasodifiy | Har doim to'g'ri |
| State management | React / MobX aralash | Har doim MobX |
| Tooltip | HTML override | Out-of-the-box |
| Dark mode | Token o'tkazib yuboradi | Har doim to'g'ri |
| Prompt hajmi | Katta (tushuntirish kerak) | Kichik (qoidalar allaqachon bor) |

### /init buyrug'idan foydalanish va uning cheklovi

```bash
# CLAUDE.md avtomatik generatsiya
claude /init

# Keyin nomini o'zgartirish (boshqa toollar uchun)
mv CLAUDE.md AGENTS.md
```

> **Diqqat:** `/init` butun codebase'ni skanerlaydi. Agar codebase'da eski va yangi pattern'lar aralash bo'lsa — eski pattern'larni ham qoidalarga kiritadi. Shuning uchun **natijani albatta ko'rib chiqing va tozalang**.

### Dizayn tizimini indekslash (katta loyihalar uchun)

Agar ichki dizayn tizimingiz alohida paket sifatida kelsa va AI uning hujjatlarini yaxshi bilmasa — Builder.io'ning **design system indexing** yechimi bor:

```markdown
## Dizayn tizimi
# Agar dizayn tizimingiz alohida paket bo'lsa:
# 1. design system indexing asbobini ishlating
# 2. U komponent namunalarini va pattern'larni topadi
# 3. LLM-ga optimallashtirilgan yo'riqnoma hosil qiladi
# 4. Natijani AGENTS.md ga qo'shing yoki havola qiling
- Dizayn tizim: `@company/ui-components`
- Komponent hujjatlari: `node_modules/@company/ui-components/README.md`
```

---

## 6. Kontekst boshqaruvi — Eng muhim cheklov

Kontekst oynasi — Claude Code'da eng muhim resurs. Kontekst to'lishi bilan Claude ishlash sifati pasayadi.

### Kontekst to'lish darajalari

| Daraja | Holat | Harakat |
|--------|-------|---------|
| 0–50% | Erkin ishlash | Hech narsa qilish shart emas |
| 50–70% | Diqqat | Kuzatib borish |
| 70–90% | Xavfli | `/compact` ishga tushirish |
| 90%+ | Kritik | `/clear` majburiy |

### Kontekst holati kuzatish

```bash
# Status liniyasini sozlash
# .claude/settings.json ga qo'shing:
{
  "statusLine": true
}
```

### Kontekst tozalash buyruqlari

```bash
/clear          # Kontekstni to'liq tozalash
/compact        # Muhim narsalarni saqlagan holda qisqartirish
/compact "API o'zgarishlarga e'tibor ber"   # Ko'rsatma bilan qisqartirish
/btw "savol"    # Kontekstga kirmaydigan qisqa savol
/rewind         # Oldingi nuqtaga qaytish
```

### Kompakt qilishni sozlash (CLAUDE.md da)

```markdown
## Kompakt qilish ko'rsatmalari
Kompakt qilishda doim quyidagilarni saqlang:
- O'zgartirilgan fayllar ro'yxati
- Test buyruqlari
- Arxitektura qarorlari
- Joriy sessiya maqsadi
```

### Kontekst eng yaxshi amaliyotlari

```bash
# ❌ Yomon — bitta sessiyada hamma narsa
claude "login bug-ni tuzat, so'ng yangi funksiya qo'sh, so'ng DB-ni optimallashtir"

# ✅ Yaxshi — har bir vazifa uchun alohida sessiya
claude "login bug-ni tuzat"
# Bajarilgandan keyin:
/clear
claude "yangi funksiya qo'sh: ..."
```

---

## 7. Agentlar (Sub-agents)

Sub-agentlar — asosiy kontekstni band qilmasdan, alohida kontekst oynasida ishlaydigan ixtisoslashgan Claude namunalari.

### Qachon agentlardan foydalanish

- Ko'p fayllarni o'rganish kerak bo'lganda
- Ixtisoslashgan e'tibor talab qilinganda
- Asosiy suhbatni toza saqlash uchun
- Kod sharhini amalga oshirishda

### Agent yaratish

```
.claude/agents/security-reviewer.md
```

```markdown
---
name: security-reviewer
description: Xavfsizlik zaifliklarini tekshirish uchun kod sharhini amalga oshiradi
tools: Read, Grep, Glob, Bash
model: opus
---
Siz yuqori malakali xavfsizlik muhandisisiz. Kodni quyidagilar uchun tekshiring:
- Injection zaifliklari (SQL, XSS, buyruq injection)
- Autentifikatsiya va avtorizatsiya kamchiliklari
- Kodda sirlar yoki ma'lumotlar
- Xavfsiz bo'lmagan ma'lumotlarni qayta ishlash

Aniq satr havolalarini va taklif etilgan tuzatishlarni bering.
```

### Agent turlari va misollari

```markdown
# .claude/agents/code-architecture-reviewer.md
---
name: code-architecture-reviewer
description: Arxitektura qarorlarini va kod tuzilmasini tekshiradi
tools: Read, Grep, Glob
model: opus
---
```

```markdown
# .claude/agents/build-error-resolver.md
---
name: build-error-resolver
description: Build xatolarini tahlil qiladi va tuzatadi
tools: Read, Bash, Edit
model: sonnet
---
```

```markdown
# .claude/agents/frontend-error-fixer.md
---
name: frontend-error-fixer
description: Frontend xatolarini tekshiradi va tuzatadi
tools: Read, Edit, Bash
model: sonnet
---
```

### Agentlardan foydalanish

```bash
# Agentni ishga tushirish
"Bu kodni xavfsizlik uchun tekshirish uchun agent ishlat"
"Autentifikatsiya tizimini tekshirish uchun sub-agent ishlat"

# Kontekstni toza saqlash uchun
"Token yangilashni qanday boshqarishimizni tekshirish uchun sub-agentlarni ishlat"
```

### Agent vs asosiy Claude

```
Asosiy Claude:
  ✓ Umumiy ishlar
  ✓ Qisqa, aniq vazifalar
  ✓ Kontekst muhim bo'lganda

Sub-agent:
  ✓ Ko'p fayl o'qish
  ✓ Ixtisoslashgan tahlil
  ✓ Asosiy kontekstni toza saqlash
  ✓ Kod sharhi (yozuvchi bilan bir xil model ishlata olmaydi)
```

> **Muhim:** Ko'p agent tizimi har doim kerak emas. Oddiy vazifalar uchun asosiy Claude yetarli.

---

## 8. Skills — Ko'nikmalar tizimi

Skills — loyihangizga, jamoangizga yoki domeningizga xos bilimlarni Claude'ga beradigan `SKILL.md` fayllari.

### Skills yaratish

```
.claude/skills/api-conventions/SKILL.md
```

```markdown
---
name: api-conventions
description: Xizmatlarimiz uchun REST API dizayn konventsiyalari
---
# API Konventsiyalari
- URL yo'llari uchun kebab-case
- JSON xususiyatlari uchun camelCase
- Ro'yxat endpoint'lari uchun har doim pagination
- URL yo'lida versiyalash (/v1/, /v2/)
- Xatolar: RFC 7807 muammo tafsilotlari
```

### Workflow skill namunasi

```markdown
---
name: fix-issue
description: GitHub issue-ni tuzatadi
disable-model-invocation: true
---
GitHub issue-ni tahlil qiling va tuzating: $ARGUMENTS.

1. `gh issue view` yordamida issue tafsilotlarini oling
2. Tasvirlangan muammoni tushuning
3. Tegishli fayllar uchun kod bazasini qidiring
4. Kerakli o'zgarishlarni amalga oshiring
5. Tuzatishni tekshirish uchun testlar yozing va ishga tushiring
6. Kodning linting va type checking-dan o'tishini ta'minlang
7. Tavsiflovchi commit xabari yarating
8. PR yarating
```

```bash
# Skillni ishga tushirish
/fix-issue 1234
```

### Skills vs CLAUDE.md

| | CLAUDE.md | Skills |
|---|-----------|--------|
| Qachon yuklanadi | Har doim, har bir sessiyada | Faqat kerak bo'lganda |
| Mos keladigan narsa | Universal qoidalar | Ixtisoslashgan bilim |
| Kontekstga ta'siri | Katta (har doim yuklanadi) | Kichik (talab bo'yicha) |

---

## 9. VS Code Agent Skills — To'liq qo'llanma

> **Manba:** VS Code Agent Skills video — GitHub Copilot + Claude bilan ishlash

Skills — bu oddiy `SKILL.md` fayllari, ammo ular **skriptlar, shablonlar va boshqa fayllarni bir joyga to'plash** imkonini beradi. Bu ularni instructions file'dan kuchliroq qiladi.

### Skills qanday ishlaydi (progressive loading)

Skills **progressiv ravishda yuklanadi** — kontekst oynasini behuda band qilmaydi:

```
1-pass: Model faqat skill NOMI va TAVSIFINI ko'radi
        → "hello-world: foydalanuvchi 'hello world' desa javob beradi"

2-pass: Model skill kerakligini aniqlaydi → SKILL.md ni o'qiydi

3-pass: SKILL.md dagi skriptlarni ishga tushiradi

4-pass: Shablonni o'qiydi va natija chiqaradi
```

Bu tuzilma sayosida SKILL.md faylda qancha ko'p fayl bo'lmasin — faqat kerak bo'lganda yuklanadi.

### Skills joylashuvi

```
loyiha/
├── .github/
│   └── skills/           ← GitHub Copilot uchun
│       └── hello-world/
│           └── SKILL.md
├── .claude/
│   └── skills/           ← Claude Code uchun
└── copilot-skills/       ← Muqobil joylashuv
```

### SKILL.md tuzilmasi

```markdown
---
name: hello-world
description: Foydalanuvchi 'hello world' deb yozganda ishga tushadi.
             Tizim ma'lumotlarini ko'rsatadi va ASCII art chiqaradi.
---

# Hello World Skill

## Workflow

### 1-qadam: Tizim ma'lumotlarini oling
Quyidagi skriptni ishga tushiring:
[./scripts/get-system-info.js](./scripts/get-system-info.js)

### 2-qadam: Javob bering
ASCII art bilan "Hello World!" deb javob bering.

### 3-qadam: Shablon bo'yicha formatlang
[./TEMPLATE.md](./TEMPLATE.md) shablonidan foydalaning.
```

### Skill fayllar tuzilmasi (modular)

```
.github/skills/my-skill/
├── SKILL.md              ← Asosiy ta'rif va workflow
├── scripts/
│   ├── get-system-info.js
│   └── validate-output.js
├── templates/
│   └── TEMPLATE.md       ← Javob shabloni
└── examples/
    ├── good-example.ts
    └── bad-example.ts    ← Yomon namuna
```

```javascript
// scripts/get-system-info.js
const os = require('os');
console.log(JSON.stringify({
  platform: os.platform(),
  type: os.type(),
  release: os.release(),
  architecture: os.arch()
}));
```

```markdown
<!-- templates/TEMPLATE.md -->
# Hello, you've triggered the Hello World skill!

```
  _    _      _ _        __          __        _     _ 
 | |  | |    | | |       \ \        / /       | |   | |
 | |__| | ___| | | ___    \ \  /\  / /__  _ __| | __| |
 |  __  |/ _ \ | |/ _ \    \ \/  \/ / _ \| '__| |/ _` |
 | |  | |  __/ | | (_) |    \  /\  / (_) | |  | | (_| |
 |_|  |_|\___|_|_|\___/      \/  \/ \___/|_|  |_|\__,_|
```

**System Info:** {system_info}

Feel free to ask if you need anything!
```

### Skill yaratish — bosqichma-bosqich

```bash
# 1. Papka yaratish
mkdir -p .github/skills/pdf-reader/scripts

# 2. Asosiy skill fayli
cat > .github/skills/pdf-reader/SKILL.md << 'EOF'
---
name: pdf-reader
description: PDF fayllarni o'qish va tahlil qilish uchun.
             Foydalanuvchi PDF yuklasa yoki PDF haqida savol bersa ishga tushadi.
---
# PDF Reader Skill

PDF faylni o'qish uchun:
1. [./scripts/extract-pdf.py](./scripts/extract-pdf.py) ni ishga tushiring
2. Mazmunini tahlil qiling va javob bering
EOF

# 3. Python skript
cat > .github/skills/pdf-reader/scripts/extract-pdf.py << 'EOF'
import sys
import subprocess
subprocess.run(['pip', 'install', 'pypdf2', '-q'])
import PyPDF2

with open(sys.argv[1], 'rb') as f:
    reader = PyPDF2.PdfReader(f)
    for page in reader.pages:
        print(page.extract_text())
EOF
```

### Skills'ni ishlatish

```bash
# VS Code'da Skills yoqish
# Settings → GitHub Copilot → Skills → Enable (experimental)

# Claude Code'da skill chaqirish
/pdf-reader  # Skill nomiga qarab avtomatik ishga tushadi

# Yoki tavsiflovchi prompt
"Bu PDF faylni o'qib menga tushuntir"
# → Model pdf-reader skill'ini avtomatik tanlaydi
```

### Qachon Skills ishlatish kerak?

```
Instructions file  → Har doim qo'llanadigan umumiy qoidalar
Prompt file        → Ko'p qayta ishlatadigan qisqa prompt'lar
Custom agent       → Aniq workflow'ni doim bajarish
Skill             → Hamma boshqa narsalar:
                    - Yangi qobiliyat o'rgatish (PDF o'qish)
                    - Domain bilim (API konventsiyalar)
                    - Murakkab workflow (deploy jarayoni)
                    - Tashqi asbob integratsiyasi
```

### Mavjud Skills kutubxonalari

```bash
# Anthropic rasmiy skills
github.com/anthropics/skills

# GitHub awesome-copilot
github.com/github/awesomecopilot

# Community (Claude Code)
# /plugin buyrug'i orqali marketplace
claude /plugin
```

---

## 10. GitHub Copilot Custom Instructions

> **Manba:** GitHub Copilot Custom Instructions video — VS Code bilan ishlash

GitHub Copilot ham xuddi AGENTS.md/CLAUDE.md kabi **custom instructions** tizimiga ega. Bu tizim jamoaga kichik prompt'lar yozish imkonini beradi.

### Sozlash: .github/copilot-instructions.md

```bash
# Fayl yaratish
mkdir -p .github
touch .github/copilot-instructions.md
```

```markdown
<!-- .github/copilot-instructions.md -->
# JavaScript kod uslubi

## O'zgaruvchi nomlash
- camelCase ishlating: `userName`, `isActive`, `totalCount`
- Boolean o'zgaruvchilar `is` yoki `has` bilan boshlaning: `isValid`, `hasError`

## Chekinish
- 2 bo'sh joy (tab emas)
- Semicolonsiz

## Funksiyalar
- Arrow function'larni afzal ko'ring
- Async/await ishlatng (Promise chain emas)
```

### Vazifaga xos yo'riqnomalar (settings.json)

Har bir Copilot funksiyasi uchun alohida yo'riqnoma sozlash mumkin:

```json
// .vscode/settings.json
{
  "github.copilot.chat.codeGeneration.instructions": [
    { "file": ".github/instructions/code-style.md" }
  ],
  "github.copilot.chat.commitMessageGeneration.instructions": [
    { "text": "Quyidagi formatda yozing: [type] tavsif. type: feat/fix/chore/docs. Emoji qo'shing 🎉✅🐛" }
  ],
  "github.copilot.chat.reviewSelection.instructions": [
    { "file": ".github/instructions/review-guide.md" }
  ],
  "github.copilot.chat.testGeneration.instructions": [
    { "file": ".github/instructions/test-guide.md" }
  ]
}
```

### Commit xabari generatsiyasi

```json
// settings.json (workspace)
{
  "github.copilot.chat.commitMessageGeneration.instructions": [
    { 
      "text": "Format: [type](scope): emoji tavsif\nTypes: feat✨ fix🐛 docs📝 style💄 refactor♻️ test✅ chore🔧\nExample: feat(auth): ✨ Google OAuth qo'shildi"
    }
  ]
}
```

### Kod ko'rib chiqish uchun yo'riqnoma

```markdown
<!-- .github/instructions/review-guide.md -->
# Kod ko'rib chiqish yo'riqnomasi

Quyidagilarni tekshiring:
1. **Xavfsizlik:** SQL injection, XSS, hardcoded secrets
2. **Ishlash:** N+1 so'rovlar, katta loop'lar, memory leak
3. **Uslub:** Kompaniya standartlari (`code-style.md`)
4. **Test:** Har bir yangi funksiya uchun test bormi?

Har bir topilgan muammo uchun:
- Aniq satr raqami
- Muammo tavsifi
- Tavsiya etilgan yechim
```

### Test generatsiyasi yo'riqnomasi

```markdown
<!-- .github/instructions/test-guide.md -->
# Test yozish qoidalari

## Framework
- Jest + React Testing Library
- AAA pattern: Arrange → Act → Assert

## Uslub
- `describe('ComponentName', () => {` tuzilmasi
- `it('should [expected behavior] when [condition]', () => {`
- Mock'larni `beforeEach` da sozlang

## Namuna
describe('UserCard', () => {
  it('should display user name when user data is provided', () => {
    // Arrange
    const user = { name: 'Ali', email: 'ali@test.com' };
    // Act
    render(<UserCard user={user} />);
    // Assert
    expect(screen.getByText('Ali')).toBeInTheDocument();
  });
});
```

### SQL schema → Prisma schema avtomatizatsiyasi

Video'da ko'rsatilgan kuchli yondashuv: Matn o'rniga **kod faylini** yo'riqnoma sifatida berish:

```json
// settings.json
{
  "github.copilot.chat.codeGeneration.instructions": [
    { "file": ".github/instructions/code-style.md" },
    { "file": "database/schema.sql" }
  ]
}
```

```bash
# Endi Copilot schema'ni biladi, shuning uchun:
"Prisma schema yarat"
# → SQL schema asosida to'liq va to'g'ri Prisma schema chiqaradi

"Foydalanuvchilar uchun CRUD API yarat"  
# → Schema'ga mos keluvchi to'g'ri API yozadi
```

### Copilot "Aussie" toni (qiziqarli misol)

Video'da ko'rsatilgan — ton va uslubni ham o'zgartirish mumkin:

```markdown
<!-- custom tone instructions -->
G'day mate! Please respond in a friendly Australian style.
Use phrases like "no worries", "reckon", "arvo" where appropriate.
Keep technical accuracy but make it fun!
```

---

## 11. Hooks — Avtomatik ishga tushuvchi skriptlar

Hooks — Claude ish jarayonida muayyan nuqtalarda skriptlarni avtomatik ishga tushiradi. CLAUDE.md ko'rsatmalaridan farqli o'laroq, hooks deterministik va kafolatli.

### Hook turlari

```json
// .claude/settings.json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          { "type": "command", "command": "npm run lint" }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "echo 'Bash buyruq ishga tushirilmoqda'" }
        ]
      }
    ]
  }
}
```

### Hook misollari

```bash
# Claude'ga hook yozdirish
"Har bir fayl tahrirlashdan keyin eslint ishga tushiradigan hook yoz"
"Migrations papkasiga yozishni bloklash uchun hook yoz"
```

```json
// Linting hook
{
  "PostToolUse": [{
    "matcher": "Edit",
    "hooks": [{ "type": "command", "command": "eslint $CLAUDE_TOOL_INPUT_FILE_PATH --fix" }]
  }]
}
```

---

## 12. MCP Serverlar

MCP (Model Context Protocol) — Claude'ni tashqi xizmatlar bilan bog'laydi.

### MCP qo'shish

```bash
# MCP server qo'shish
claude mcp add

# Mashhur MCP serverlar
# GitHub
claude mcp add github

# Notion
claude mcp add notion

# Figma
claude mcp add figma
```

### MCP ishlatish misollari

```bash
# Issue tracker bilan ishlash
"Asana-dan ochiq vazifalarni olib kel va eng muhimini tuzat"

# Ma'lumotlar bazasi
"Foydalanuvchilar jadvalidagi so'nggi 10 ta yozuvni ko'rsat"

# Figma
"Bu Figma freymi dizaynini React komponentga aylantir"
```

> **Diqqat:** Agar 20,000 tokendan ko'proq MCP kontekst ishlatilsa, Claude'ning ishlash sifati pasayadi. MCP serverlarni ehtiyotkorlik bilan qo'shing.

---

## 13. Slash Commands — Maxsus buyruqlar

```
.claude/commands/tech-debt.md
.claude/commands/context-dump.md
.claude/commands/analytics.md
```

### Command yaratish

```markdown
# .claude/commands/review-pr.md
---
name: review-pr
description: PR-ni ko'rib chiqadi va sharh beradi
---
Joriy branchdagi o'zgarishlarni ko'rib chiqqin:

1. `git diff main` ni ishga tushir
2. O'zgarishlarni arxitektura, xavfsizlik, va ishlash uchun ko'rib chiq
3. Muammolarni aniq satr havolalari bilan sanab ber
4. Yaxshilanishlarni taklif et
```

```bash
# Ishga tushirish
/review-pr
```

### Command vs Skills farqi

Kunlik routine workflow → **Command** (tez chaqiruv)
Ixtisoslashgan bilim bazasi → **Skill** (kontekst boyitish)

---

## 14. Ish jarayoni va optimal workflow

### Asosiy workflow: Explore → Plan → Implement → Commit

```
1. Plan Mode (Ctrl+G) — fayllarni o'qish, o'zgartirmasdan
2. Rejalashtirish — aniq amalga oshirish rejasi yaratish
3. Implement Mode — kod yozish, testlarni ishga tushirish
4. Commit — tavsiflovchi commit va PR
```

### Plan Mode ishlatish

```bash
# Plan mode'ni ishga tushirish
Ctrl+G  # yoki
/plan

# Plan mode'da so'rov
"src/auth papkasini o'qing va sессияlarni qanday boshqarishimizni tushuning"
"Google OAuth qo'shmoqchiman. Qaysi fayllar o'zgarishi kerak? Reja tuzing."

# Kodni amalga oshirish
# Plan Mode-ni o'chirish va Normal Mode-ga o'tish
"OAuth oqimini rejangizdan amalga oshiring. Testlar yozing."
```

### Katta funksiyalar uchun: Intervyu usuli

```bash
"[Qisqa tavsif] qurishni xohlayman. Meni AskUserQuestion asboti yordamida batafsil so'rog'ingiz.

Texnik amalga oshirish, UI/UX, chekka holatlar, muammolar va murosalar haqida so'rang. 
Aniq savollarni bermang, menimcha ko'rmagan qiyin tomonlarini qidiring.

Hamma narsani yoritib bo'lguningizcha so'rashni davom eting, so'ng to'liq spesifikatsiyani SPEC.md ga yozing."
```

### Kursni erta tuzatish

```bash
Esc          # Claude'ni o'rtasida to'xtatish (kontekst saqlanadi)
Esc + Esc    # Rewind menyusini ochish
/rewind      # Oldingi holatlarga qaytish
"Buni bekor qil"  # Claude o'zgarishlarini qaytarish
/clear       # Bog'liq bo'lmagan vazifalar orasida kontekstni tozalash
```

---

## 15. Parallel sessiyalar va avtomatlashtirish

### Non-interactive rejim

```bash
# Bitta so'rov
claude -p "Bu loyiha nima qilishini tushuntir"

# Skriptlar uchun strukturlangan natija
claude -p "Barcha API endpoint'larini sanab ber" --output-format json

# Real-time qayta ishlash
claude -p "Bu log faylini tahlil qil" --output-format stream-json

# Ruxsatlarni cheklash
claude -p "login.ts-ni tuzat" --allowedTools "Edit,Bash(npm test)"
```

### Parallel sessiyalar

```bash
# Writer/Reviewer pattern
# Sessiya A (Yozuvchi)
claude "API endpoint'larimiz uchun rate limiter yaratish"

# Sessiya B (Ko'rib chiquvchi) — boshqa terminalda
claude "src/middleware/rateLimiter.ts dagi rate limiter amalga oshirishni ko'rib chiq. 
Chekka holatlarni, race condition va mavjud middleware pattern-larni tekshir."
```

### Katta migratsiyalar uchun fan-out

```bash
# 1. Vazifalar ro'yxatini yarating
claude -p "React-dan Vue-ga o'tkazish kerak bo'lgan barcha 2000 Python faylini sanab ber" > files.txt

# 2. Har bir fayl uchun parallel ishga tushirish
for file in $(cat files.txt); do
  claude -p "\"$file\"ni React-dan Vue-ga migratsiya qiling. OK yoki FAIL qaytaring." \
    --allowedTools "Edit,Bash(git commit *)" &
done

# 3. Auto mode — uzluksiz bajarish uchun
claude --permission-mode auto -p "barcha lint xatolarini tuzat"
```

### Agent jamoalari (Agent Teams)

```bash
# Avtomatlashtirilgan bir nechta sessiyalarni koordinatsiya
# Claude Code desktop app orqali yoki
# code.claude.com da cloud'da
```

---

## 16. Xavfsizlik va ruxsatlar

### Ruxsat rejimlari

```bash
# Standart — har bir muammoli harakat uchun so'rash
claude  # default

# Auto mode — classifier ko'rib chiqadi, faqat xavfli narsalarni bloklaydi
claude --permission-mode auto

# Sandbox — OS darajasida izolyatsiya
# .claude/settings.json da:
{ "sandbox": true }
```

### Ruxsatlar ro'yxati

```bash
# Xavfsiz buyruqlarga ruxsat berish
/permissions

# Muayyan buyruqlarga ruxsat
# .claude/settings.json:
{
  "allowedTools": ["Edit", "Read", "Bash(npm run lint)", "Bash(git commit *)"]
}
```

### Xavfsizlik uchun hooks

```json
{
  "PreToolUse": [{
    "matcher": "Bash",
    "hooks": [{
      "type": "command",
      "command": "echo 'Bash buyruq tekshirilmoqda: ' $CLAUDE_TOOL_INPUT"
    }]
  }]
}
```

---

## 17. Xatolardan qochish

### ❌ Eng keng tarqalgan xatolar

```
1. "Kitchen sink sessiya"
   Muammo: Bitta sessiyada bogʻliq boʻlmagan ko'p vazifa
   Yechim: /clear ni bogʻliq boʻlmagan vazifalar orasida ishlat

2. "Qayta-qayta tuzatish"
   Muammo: Xuddi shu xato uchun 3+ marta tuzatish
   Yechim: Ikki marta muvaffaqiyatsiz tuzatishdan keyin /clear
           Nima o'rgangingizni qo'shgan holda yangi, aniq prompt bilan boshlang

3. "Haddan tashqari CLAUDE.md"
   Muammo: CLAUDE.md juda uzun — muhim qoidalar yo'qoladi
   Yechim: Qattiq qisqartirish. Claude allaqachon to'g'ri qilayotgan narsalarni o'chiring.

4. "Ishonch-keyin-tekshirish tafovuti"
   Muammo: Chekka holatlarni ko'rib chiqmaydigan amalga oshirish
   Yechim: Har doim tasdiqlashni ta'minlang (testlar, skriptlar, skrinshotlar)

5. "Cheksiz tadqiqot"
   Muammo: "Tekshiring" - Claude 100+ faylni o'qiydi, kontekst to'lib ketadi
   Yechim: Tadqiqotni qisqartiring YOKI sub-agentlardan foydalaning
```

### ✅ Eng yaxshi amaliyotlar

```bash
# Tasdiqlash bilan yaxshi prompt
❌ "email manzillarni tekshiradigan funksiya yarating"
✅ "validateEmail funksiyasini yozing. Sinov holatlari: user@example.com true,
    invalid noto'g'ri, @no.com noto'g'ri. Amalga oshirgandan keyin testlarni ishga tushiring"

# Aniq kontekst
❌ "login bug-ni tuzat"
✅ "Foydalanuvchilar session timeout dan keyin login muvaffaqiyatsiz ekanligini bildirishadi.
    src/auth/-dagi auth oqimini, ayniqsa token yangilashni tekshiring.
    Muammoni takrorlaydigan muvaffaqiyatsiz test yozing, keyin tuzating"

# Namunalarga havola
❌ "calendar widget qo'sh"
✅ "Bosh sahifadagi mavjud vidjetlar qanday amalga oshirilganini ko'ring.
    HotDogWidget.php yaxshi namuna. Foydalanuvchi oy tanlab, yil bo'yicha navigatsiya
    qilishi mumkin bo'lgan yangi calendar widget uchun pattern-ga amal qiling."
```

---

## 18. Model tanlash strategiyasi

| Model | Mos kelishi | Narxi |
|-------|-------------|-------|
| **Opus** | Murakkab arxitektura qarorlari, chuqur kod sharhi | Yuqori |
| **Sonnet** | Kundalik amalga oshirish, eng yaxshi tezlik/sifat balansi | O'rta |
| **Haiku** | Tez tuzatishlar, formatlash, takrorlanadigan vazifalar | Arzon |

### Agent uchun model tanlash

```markdown
# .claude/agents/security-reviewer.md
---
model: opus          # Xavfsizlik uchun eng yaxshi model
tools: Read, Grep
---

# .claude/agents/quick-fixer.md
---
model: haiku         # Oddiy tuzatishlar uchun tezroq va arzonroq
tools: Edit
---
```

---

## 19. Tayyor shablonlar

### Shablon 1: To'liq AGENTS.md (Builder.io uslubi)

```markdown
# AGENTS.md

## ✅ DO — Qiling
- MUI v5 ishlating
- Emotion CSS `styled()` formatida: `const El = styled('div')(...)`
- State uchun MobX ishlating
- Dizayn tokenlarini ishlating: `theme.palette.primary.main`
- Grafiklar uchun ApexCharts
- Komponent out-of-the-box imkoniyatlarini ishlating

## ❌ DON'T — Qilmang
- Ranglarni hardcode qilmang (`#FF0000` → token ishlating)
- HTML tooltip override yaratmang
- Class-based komponent yozmang
- `<div>` ishlatmang — `<Box>` yoki `<Stack>` ishlating

## Fayl tekshirish (to'liq build emas!)
- TypeScript: `npx tsc --noEmit src/path/to/file.ts`
- Lint: `npx eslint src/path/to/file.ts --fix`
- To'liq build: `yarn build app` (faqat kerak bo'lganda)

## Loyiha tuzilmasi
- Route'lar: `app.tsx`
- Sidebar: `app-sidebar` (nomiga qarab qidiradi)
- Komponentlar: `app/components/`
- Store'lar: `app/stores/`
- Tokenlar: `src/theme/tokens.ts`
- API: `src/api/`

## ✅ Yaxshi namunalar
- Funksional komponent: `projects.tsx`
- MobX store: `user-store.ts`
- Dashboard: `analytics-dashboard.tsx`
- Form: `user-settings-form.tsx`

## ❌ Yomon namunalar (qochish)
- Class komponent: `get-admin.tsx`

## API hujjatlari
- `docs/api-reference.md` ni ko'ring
- Autentifikatsiya: JWT Bearer token
```

### Shablon 2: Web ilovasi uchun CLAUDE.md

```markdown
# Loyiha: [Loyiha nomi]

## Stek
- Next.js 14, TypeScript, Tailwind CSS
- PostgreSQL, Prisma ORM
- Jest + Playwright (testlar)

## Buyruqlar
- O'rnatish: `npm install`
- Dev: `npm run dev`
- Test: `npm test`
- Bitta test: `npm test -- -t "test nomi"`
- Build: `npm run build`
- Lint: `npm run lint`

## Kod qoidalari
- Import/export (CommonJS emas)
- Single quotes
- Komponentlar uchun: `src/components/`
- API yo'llari uchun: `src/app/api/`

## Muhim
- HECH QACHON sirlarni kodga yozma
- PR oldidan lint va test bajar
- Migratsiyalarni to'g'ridan-to'g'ri tahrirlama
```

### Shablon 3: Xavfsizlik agenti

```markdown
---
name: security-audit
description: Kodni xavfsizlik zaifliklariga tekshiradi
tools: Read, Grep, Glob
model: opus
---
Yuqori malakali xavfsizlik muhandisi sifatida quyidagilarni tekshiring:

1. Injection zaifliklari (SQL, XSS, command injection)
2. Autentifikatsiya/avtorizatsiya kamchiliklari
3. Kodda qattiq kodlangan sirlar
4. Xavfsiz bo'lmagan deserialization
5. Ochiq qayta yo'naltirish

Har bir muammo uchun:
- Aniq fayl va satr raqami
- Zaiflikning tavsifi
- Tavsiya etilgan tuzatish
- CVSS jiddiylik darajasi (Muhim/Yuqori/O'rta/Past)
```

### Shablon 4: CI/CD pipeline uchun

```bash
#!/bin/bash
# claude-ci.sh

# Fayllarni tahlil qilish
claude -p "src/-dagi barcha TypeScript fayllarini ko'rib chiq" \
  --output-format json \
  --allowedTools "Read,Grep,Glob"

# Avtomatik migratsiya
for file in $(find src/ -name "*.js" -not -path "*/node_modules/*"); do
  claude -p "\"$file\"ni TypeScript-ga aylantir. OK yoki FAIL qaytaring." \
    --allowedTools "Edit,Bash(npm run type-check)" \
    --permission-mode auto
done
```

### Shablon 5: SPEC.md yaratish uchun prompt

```
[Qisqa tavsif] ni qurmoqchiman. Meni AskUserQuestion asboti yordamida batafsil so'roq qiling.

Quyidagilar haqida so'rang:
- Texnik amalga oshirish
- UI/UX
- Chekka holatlar va xatolarni qayta ishlash
- Muhit va bog'liqliklar
- Ishlash talablari
- Xavfsizlik mulohazalari

Aniq savollarni bermang — menimcha ko'rmagan qiyin tomonlarni qidiring.
Hamma narsani yoritib bo'lguningizcha so'rashni davom eting, so'ng to'liq spesifikatsiyani SPEC.md ga yozing.

Spec tugagandan so'ng — uni amalga oshirish uchun yangi sessiyani boshlang.
```

### Shablon 6: VS Code GitHub Copilot settings.json

```json
{
  "github.copilot.chat.codeGeneration.instructions": [
    { "file": ".github/instructions/code-style.md" },
    { "file": "database/schema.sql" }
  ],
  "github.copilot.chat.commitMessageGeneration.instructions": [
    { "text": "Format: [type](scope): emoji tavsif\nTypes: feat✨ fix🐛 docs📝 refactor♻️ test✅ chore🔧" }
  ],
  "github.copilot.chat.reviewSelection.instructions": [
    { "file": ".github/instructions/review-guide.md" }
  ],
  "github.copilot.chat.testGeneration.instructions": [
    { "file": ".github/instructions/test-guide.md" }
  ]
}

---

## 📁 Tavsiya etilgan loyiha tuzilmasi

```
loyiha/
├── CLAUDE.md                    ← Asosiy konfiguratsiya (Claude Code)
├── AGENTS.md                    ← Universal standart (barcha agentlar)
├── CLAUDE.local.md              ← Shaxsiy sozlamalar (.gitignore)
├── .github/
│   ├── copilot-instructions.md  ← GitHub Copilot umumiy yo'riqnoma
│   ├── skills/                  ← VS Code Copilot skills
│   │   └── my-skill/
│   │       ├── SKILL.md
│   │       └── scripts/
│   └── instructions/
│       ├── code-style.md
│       ├── review-guide.md
│       └── test-guide.md
├── .claude/
│   ├── settings.json            ← Hooks, ruxsatlar
│   ├── agents/
│   │   ├── security-reviewer.md
│   │   ├── code-reviewer.md
│   │   └── frontend-fixer.md
│   ├── skills/                  ← Claude Code skills
│   │   ├── api-conventions/
│   │   │   └── SKILL.md
│   │   └── deployment/
│   │       └── SKILL.md
│   └── commands/
│       ├── review-pr.md
│       ├── fix-issue.md
│       └── tech-debt.md
├── .vscode/
│   └── settings.json            ← Copilot custom instructions sozlamalari
└── src/
    └── CLAUDE.md                ← Papkaga xos qoidalar
```

---

## 🔗 Foydali havolalar

- **Rasmiy hujjatlar:** https://code.claude.com/docs/en/overview
- **Eng yaxshi amaliyotlar:** https://code.claude.com/docs/en/best-practices
- **AGENTS.md standarti:** https://agents.md
- **CLAUDE.md yozish bo'yicha:** https://www.humanlayer.dev/blog/writing-a-good-claude-md
- **Ultimate Guide (GitHub):** https://github.com/FlorianBruniaux/claude-code-ultimate-guide
- **50 ta maslahat:** https://agentsroom.dev/claude-code-tips
- **Anthropic rasmiy skills:** https://github.com/anthropics/skills
- **GitHub awesome-copilot:** https://github.com/github/awesomecopilot

---

*Oxirgi yangilanish: 2026-yil aprel | Claude Code 2.0+ · VS Code Copilot Skills · Builder.io amaliyot asosida*
