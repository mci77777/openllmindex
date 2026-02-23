# ROADMAP

## v0.1.x

**已发布**: `openllmindex 0.1.0` / `@llmindex/schema 0.1.0`

### 已完成

- [x] CLI 功能完善（init / verify / status / YAML config / templates / URL check）
- [x] 规范正式化（spec.md + spec.zh.md，移除 Draft 标记，含 Changelog/Security）
- [x] 质量加固（100+ 测试、CLI 集成测试、≥85% 覆盖率、Ruff lint CI）
- [x] JSON Schema 完整文档化（description/$comment 字段覆盖所有属性）
- [x] Test vectors（8 个 valid/invalid 向量）
- [x] PyPI 和 npm 双包发布，tag-based CI/CD 自动化
- [x] 3 个行业示例（ecommerce / local-business / saas）

### 待完成 (v0.1.1)

- [x] 更多行业示例：`blog/`、`restaurant/`、`marketplace/`
- [x] `docs/index.html` 更新（同步 CLI 用法和当前规范）

---

## v0.2.x (当前稳定版)

> 已发布：`openllmindex 0.2.0` — 扩展 manifest 表达能力，面向真实生产部署的完整性。

### 特性规划

#### 1. 多语言 manifest [x]

**动机**：全球化站点需要为不同语言的 AI Agent 提供本地化内容。

**Schema 变更**（向后兼容）：
```json
{
  "language": "zh-CN",
  "languages": ["zh-CN", "en"],
  "localized_endpoints": {
    "en": {
      "products": "https://example.com/en/llm/products",
      "about": "https://example.com/en/llm/about"
    },
    "zh-CN": {
      "products": "https://example.com/zh/llm/products",
      "about": "https://example.com/zh/llm/about"
    }
  }
}
```

**CLI 支持**：`generate --language zh-CN --language en`

---

#### 2. `access_control` 字段 [x]

**动机**：允许站点声明哪些 AI 系统可以使用数据，以及访问限制。

**Schema 变更**（新增可选字段）：
```json
{
  "access_control": {
    "allow": ["*"],
    "deny": ["BadBot/1.0"],
    "rate_limit": "1000/day",
    "requires_attribution": true,
    "commercial_use": "allowed"
  }
}
```

**枚举值设计**：
- `allow`: `["*"]` 全部 | `["GPTBot", "ClaudeBot"]` 白名单
- `commercial_use`: `"allowed"` | `"non-commercial"` | `"contact-required"`

---

#### 3. EdDSA JWS 签名 [x]

**动机**：允许 AI Agent 验证 manifest 来源真实性，防篡改。

**Schema 变更**（`sig` 字段已在 v0.1 schema 中定义，v0.2 提供实现）：
```json
{
  "sig": {
    "alg": "EdDSA",
    "kid": "https://example.com/.well-known/llmindex-key.json",
    "jws": "eyJhbGciOiJFZERTQSJ9..."
  }
}
```

**CLI 支持**：
```bash
llmindex sign keygen --output keys/
llmindex sign manifest --key keys/private.pem .well-known/llmindex.json
llmindex sign verify --key keys/public.pem .well-known/llmindex.json
```

**依赖**：`cryptography>=42.0`（可选 extra）

---

#### 4. 增量更新支持 [x]

**动机**：大型产品目录频繁全量发布代价高，需要增量机制。

**方案**：
- `feeds` 中新增 `products_jsonl_delta`（仅包含自 `since` 以来的变更）
- manifest 新增 `feed_updated_at` 字段（feed 最后更新时间，独立于 manifest）

```json
{
  "feeds": {
    "products_jsonl": "https://example.com/llm/feed/products.jsonl",
    "products_jsonl_delta": "https://example.com/llm/feed/products-delta.jsonl?since={timestamp}"
  },
  "feed_updated_at": "2026-02-22T10:00:00Z"
}
```

---

#### 5. CLI watch 模式（v0.2.1）[x]

**动机**：开发阶段自动监听源数据（CSV/JSON），变更后自动重建 artifacts。

**实现**：
```bash
llmindex watch --config llmindex.yaml --output-dir dist
# 监听 products.csv 变化 → 自动重建 llmindex.json + products.jsonl + *.md
```

**依赖**：`watchfiles>=0.21`（可选 extra）

---

#### 6. 规范示例库扩展 [x]

**交付**：22 个行业 manifest 示例 + JSONL feed，覆盖 v0.1（10 个）和 v0.2（12 个）：

| v0.1 示例 | v0.2 示例 |
|-----------|-----------|
| blog, gaming, kids | automotive, beauty, ecommerce |
| local-business, marketplace | education, fintech, fitness |
| nonprofit, pet | food-beverage, healthcare |
| real-estate, restaurant, saas | home-decor, jewelry, travel, wellness |

---

### v0.2 向后兼容性

| 变更类型 | 内容 | 兼容性 |
|----------|------|--------|
| 新增字段 | `languages`、`localized_endpoints`、`access_control`、`feed_updated_at` | ✅ 完全向后兼容（可选字段）|
| Schema 版本 | `"version": "0.2"` | ⚠️ 旧 v0.1 schema 不验证新字段 |
| CLI 参数 | 新增 `--language`（多次）、`sign`、`watch` 子命令 | ✅ 现有命令不变 |
| npm 包 | `@llmindex/schema` 新增 v0.2 类型定义 | ✅ v0.1 类型保留 |

---

### v0.2 新增依赖

| 依赖 | Extra | 用途 |
|------|-------|------|
| `cryptography>=42.0` | `[sign]` | EdDSA JWS 签名生成/验证 |
| `watchfiles>=0.21` | `[watch]` | CLI watch 模式文件监听 |

---

## v1.0 (稳定版)

> 目标：生产级稳定性、生态互通、官方服务。

- **向后兼容保证**：semver 稳定，含迁移指南
- **conformance test suite**：标准化测试向量，供第三方实现自验证
- **官方 validator service**：在线校验 API（`https://validate.llmindex.org`）
- **多语言 SDK**：
  - `openllmindex` (Python) — 当前已有
  - `@llmindex/sdk` (TypeScript/Node) — 读取/生成/验证/签名
  - `llmindex-go` (Go) — 轻量级验证/读取库

---

## 版本发布计划

| 版本 | 预计内容 | 状态 |
|------|----------|------|
| v0.1.0 | CLI 完整 + 规范正式化 + 双包发布 | ✅ 已发布 |
| v0.1.1 | 更多行业示例 + docs site 更新 | ✅ 已完成 |
| v0.2.0 | 多语言 + access_control + EdDSA 签名 + 增量更新 + CLI watch + 22 行业示例 | ✅ 已发布 |
| v1.0.0 | 稳定版 + SDK + validator service | 📋 远期 |
