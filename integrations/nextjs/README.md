# llmindex — Next.js Integration

Serve your `llmindex.json` manifest and `/llm/*` pages from a Next.js application.

## Option 1: Static Files (Recommended)

Place your files in the `public/` directory:

```
public/
├── .well-known/
│   └── llmindex.json
└── llm/
    ├── products.md
    ├── policies.md
    ├── faq.md
    ├── about.md
    └── feed/
        └── products.jsonl
```

Next.js serves everything in `public/` as static files. No code needed.

## Option 2: API Routes (Dynamic)

If you need to generate the manifest dynamically (e.g., from a database):

### App Router (Next.js 13+)

```typescript
// app/.well-known/llmindex.json/route.ts
import { NextResponse } from "next/server";

export async function GET() {
  const manifest = {
    version: "0.1",
    updated_at: new Date().toISOString(),
    entity: {
      name: process.env.SITE_NAME || "My Site",
      canonical_url: process.env.SITE_URL || "https://example.com",
    },
    language: "en",
    topics: ["your-industry"],
    endpoints: {
      products: `${process.env.SITE_URL}/llm/products`,
      policies: `${process.env.SITE_URL}/llm/policies`,
      faq: `${process.env.SITE_URL}/llm/faq`,
      about: `${process.env.SITE_URL}/llm/about`,
    },
  };

  return NextResponse.json(manifest, {
    headers: {
      "Cache-Control": "public, max-age=3600",
    },
  });
}
```

### Markdown Pages with MDX

```typescript
// app/llm/products/page.tsx
import { readFile } from "fs/promises";
import { join } from "path";

export default async function ProductsPage() {
  const content = await readFile(
    join(process.cwd(), "content/llm/products.md"),
    "utf-8"
  );

  return (
    <article>
      <pre>{content}</pre>
    </article>
  );
}
```

## Option 3: Middleware (Rewrite Rules)

If your llmindex files are hosted elsewhere (CDN, S3), use middleware to proxy:

```typescript
// middleware.ts
import { NextRequest, NextResponse } from "next/server";

const LLMINDEX_CDN = process.env.LLMINDEX_CDN_URL || "";

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (pathname === "/.well-known/llmindex.json") {
    return NextResponse.rewrite(new URL("/llmindex.json", LLMINDEX_CDN));
  }

  if (pathname.startsWith("/llm/")) {
    return NextResponse.rewrite(new URL(pathname, LLMINDEX_CDN));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/.well-known/llmindex.json", "/llm/:path*"],
};
```

## Validation Helper

Use `@llmindex/schema` to validate your manifest at build time:

```typescript
// scripts/validate-llmindex.ts
import Ajv from "ajv";
import addFormats from "ajv-formats";
import schema from "@llmindex/schema";
import manifest from "../public/.well-known/llmindex.json";

const ajv = new Ajv();
addFormats(ajv);
const validate = ajv.compile(schema);

if (!validate(manifest)) {
  console.error("Invalid llmindex.json:", validate.errors);
  process.exit(1);
}

console.log("llmindex.json is valid!");
```

Add to `package.json`:

```json
{
  "scripts": {
    "validate:llmindex": "tsx scripts/validate-llmindex.ts"
  }
}
```
