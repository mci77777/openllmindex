# llmindex 规范 v0.1

> **状态**: v0.1.0
> **固定入口**: `/.well-known/llmindex.json`
> **目标**: 为 LLM、AI 搜索引擎和爬虫提供一个机器可读的索引，用于发现并理解网站的关键信息。

## 1. 概述

llmindex 是一个轻量级规范，在固定的 well-known URL 上定义一个标准化的 JSON manifest。它相当于为 LLM agent 提供的“目录”，告诉它们到哪里去获取产品、政策、FAQ 以及网站的其他结构化信息。

**设计原则**:
- 极简: ≤10 个顶层字段
- 可发现: 固定的 well-known 路径
- 可验证: 可选的域名所有权证明与密码学签名
- 可版本化: 语义化版本控制，并提供向后兼容保证

## 2. 入口点

```
GET /.well-known/llmindex.json
Content-Type: application/json; charset=utf-8
```

服务端 SHOULD 通过以下方式支持条件请求:
- 使用 `ETag` 头进行基于内容的缓存
- 使用 `Last-Modified` 头进行基于时间的缓存
- 使用 `Cache-Control` 头（推荐: `max-age=3600, must-revalidate`）

## 3. 字段定义

### 3.1 必选字段

| 字段 | 类型 | 说明 |
|-------|------|-------------|
| `version` | string | 规范版本。对本版本 MUST 为 `"0.1"`。 |
| `updated_at` | string | ISO 8601 datetime（推荐 UTC）。表示 manifest 的最后更新时间。 |
| `entity` | object | 该 manifest 所描述的实体。 |
| `entity.name` | string | 实体的展示名称（公司、品牌、个人）。 |
| `entity.canonical_url` | string (URI) | 规范的主页 URL。MUST 为有效的 HTTPS URL。 |
| `language` | string | 主语言，BCP-47 格式（如 `"en"`, `"zh-CN"`, `"ja"`）。 |
| `topics` | array[string] | 描述实体所属领域的类目标签。至少需要 1 个。 |
| `endpoints` | object | 指向人类/机器可读信息页的 URL。 |
| `endpoints.products` | string (URI) | 产品列表页 URL。 |
| `endpoints.policies` | string (URI) | 政策页 URL（物流、退换货、质保、支付等）。 |
| `endpoints.faq` | string (URI) | FAQ 页面 URL。 |
| `endpoints.about` | string (URI) | 关于/公司信息页 URL。 |

### 3.2 可选字段

| 字段 | 类型 | 说明 |
|-------|------|-------------|
| `feeds` | object | 机器可读的数据 feed。 |
| `feeds.products_jsonl` | string (URI) | 指向包含产品数据的 JSONL 文件的 URL（推荐）。 |
| `feeds.offers_json` | string (URI) | 指向包含当前优惠/促销信息的 JSON 文件的 URL。 |
| `verify` | object | 域名所有权验证信息。 |
| `verify.method` | string | 验证方式: `"dns_txt"` 或 `"http_file"`。 |
| `verify.value` | string | challenge 值（DNS TXT 记录内容）或 proof 文件名。 |
| `sig` | object | manifest 的密码学签名。 |
| `sig.alg` | string | 签名算法（推荐: `"EdDSA"`）。 |
| `sig.kid` | string | 用于查找公钥的 key identifier。 |
| `sig.jws` | string | 已签名 manifest 的 JWS Compact Serialization。 |
| `license` | string | 许可标识符（SPDX 格式）或许可证文本 URL。 |

## 4. /llm 页面

`endpoints` 对象指向为 LLM 优化的页面。这些页面 SHOULD:
- 无需鉴权即可访问
- 使用干净、结构化的标记（Markdown 或结构良好的 HTML）
- 包含事实性、最新的信息
- 避免重度依赖 JavaScript 渲染（内容应出现在初始 HTML/Markdown 中）

### 4.1 必须页面

| 页面 | 路径（推荐） | 内容 |
|------|---------------------|---------|
| Products | `/llm/products` | 按类别分组的产品列表，包含名称、价格、分类和链接。 |
| Policies | `/llm/policies` | 物流、退换货、质保与支付政策。 |
| FAQ | `/llm/faq` | 按主题组织的常见问题。 |
| About | `/llm/about` | 品牌故事、公司信息、联系方式。 |

## 5. products.jsonl Feed 格式

每一行都是一个 JSON 对象，字段如下:

| 字段 | 类型 | 必填 | 说明 |
|-------|------|----------|-------------|
| `id` | string | Yes | 唯一产品标识符。 |
| `title` | string | Yes | 产品展示名称。 |
| `url` | string (URI) | Yes | 产品页面 URL。 |
| `image_url` | string (URI) | No | 产品主图 URL。 |
| `price` | number | Yes* | 产品价格。若 `price_range` 缺失则必填。 |
| `currency` | string | Yes* | ISO 4217 货币代码。与 `price` 同时必填。 |
| `price_range` | object | No | `price` 的替代方案: `{"min": number, "max": number, "currency": string}`。 |
| `availability` | string | Yes | 取值之一: `"in_stock"`, `"out_of_stock"`, `"preorder"`。 |
| `brand` | string | No | 品牌名称。 |
| `category` | string | No | 产品分类。 |
| `updated_at` | string | Yes | 产品最后更新时间的 ISO 8601 datetime。 |

*必须存在 `price` + `currency` 或 `price_range` 二者之一。

## 6. 验证

### 6.1 DNS TXT 验证

在域名的 DNS 中添加 TXT 记录:
```
_llmindex-challenge.example.com TXT "challenge-value-here"
```

将 `verify.method` 设为 `"dns_txt"`，并将 `verify.value` 设为 challenge 字符串。

### 6.2 HTTP 文件验证

在如下路径放置 proof 文件:
```
GET /.well-known/llmindex-proof.txt
```

文件内容 MUST 与 `verify.value` 相同。将 `verify.method` 设为 `"http_file"`。

### 6.3 签名（可选）

为了防篡改，可以使用 JWS 对 canonical JSON（key 排序、无空白）进行签名:
- 推荐算法: `EdDSA`（Ed25519）
- `sig.jws` 字段包含 JWS Compact Serialization
- Validator MUST 使用已发布的公钥（由 `sig.kid` 标识）验证签名

## 7. 版本策略

- **0.x 版本**: minor 版本之间允许破坏性变更。客户端 SHOULD 检查 `version` 字段。
- **1.0+**: 仅允许向后兼容的变更。可以新增可选字段；不会移除既有字段或改变其语义。
- **版本协商**: 客户端读取 `version` 字段，并按对应版本规则解析。

## 8. 兼容性

实现者 MAY 生成 `/llms.txt` 作为兼容层，适配期望该文件的工具。但 `/.well-known/llmindex.json` 是规范的 entry point。

## 9. 错误处理

| 场景 | 期望行为 |
|----------|-------------------|
| `/.well-known/llmindex.json` 返回 404 | 站点不支持 llmindex。 |
| `/.well-known/llmindex.json` 返回非 JSON | 视为不支持；记录 warning。 |
| `version` 字段不可识别 | 尝试尽最大努力解析；对未知字段给出 warning。 |
| `endpoints.*` URL 返回 404/5xx | 将该 endpoint 标记为不可用；继续处理其他 endpoint。 |
| `feeds.*` URL 不可访问 | 跳过 feed；改为依赖 endpoint 页面。 |

## 10. 安全考虑

- **需要 HTTPS**: manifest MUST 通过 HTTPS 提供，并且 `entity.canonical_url` MUST 为 HTTPS URL。实现者 SHOULD 为所有 `endpoints.*` 与 `feeds.*` URL 使用 HTTPS。
- **manifest 中不得包含敏感信息**: 实现者 MUST NOT 在 manifest 中包含认证 token、API key、会话标识符或其他敏感信息（包括 URL query string 中的参数）。
- **`robots.txt` 建议**: 如果你希望 AI agent 发现并读取 llmindex 内容，请不要在 `robots.txt` 中屏蔽 `/.well-known/llmindex.json` 或被引用的 `/llm/*` endpoint。如果你不希望自动化访问，请使用 `robots.txt` 和/或其他访问控制手段限制抓取。

## 11. IANA 考虑

本规范使用现有的 `application/json` media type，不需要新增任何 IANA 注册项。

## 12. 更新记录

- **v0.1.0 (2025-02-22)** — 初始发布。
