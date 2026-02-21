# OpenLLMIndex 核心库 — 开发编排计划

> 本文档规划「核心库功能完善」「规范文档正式化」「质量加固」「路线图」四个方向的任务分解与执行顺序。
> 所有任务在 `openllmindex` 仓库执行。

---

## 当前状态摘要

| 模块 | 状态 | 关键问题 |
|------|------|----------|
| CLI (generate/validate) | 可用 | 缺少 `verify` 子命令、`init` 子命令 |
| Importers (CSV/JSON/Shopify) | 可用 | 缺少 YAML config 导入、边界处理可改进 |
| Validators | 可用 | 无 feed URL 可达性检查 |
| Spec (spec.md) | Draft 状态 | 需正式化、补中文版、完善 changelog |
| JSON Schema | 可用 | 缺 `$comment` 注释、缺独立 feed schema 文件 |
| Tests | 50+ cases | 缺 CLI 集成测试（typer CliRunner） |
| npm (@llmindex/schema) | 可用 | 类型定义完整但无验证函数 |
| demo.py | 有 bug | 路径 `cli/` → `llmindex/` 未更新 |
| docs site | 单页 HTML | 内容可能滞后 |

---

## 执行阶段

### Stage 0: 紧急修复 (Hotfix)

> 优先级最高，修复已知 broken 的代码。

| # | 任务 | 文件 | 说明 |
|---|------|------|------|
| 0.1 | 修复 demo.py 路径 bug | `examples/demo.py:38` | `cli/` → `llmindex/` |
| 0.2 | commit portal 原型 | `portal-prototype/`, `design-system/` | 当前 staged + untracked 文件需要 commit |

**预估**: 单次 commit 即可完成。

---

### Stage 1: 质量加固

> 在添加新功能之前，先巩固现有代码的测试覆盖和质量。

| # | 任务 | 范围 | 说明 |
|---|------|------|------|
| 1.1 | CLI 集成测试 | `llmindex/tests/test_cli.py` (新建) | 使用 typer `CliRunner` 测试 `generate`、`validate`、`version` 三个子命令的 happy path + error path |
| 1.2 | 测试覆盖率报告 | `pyproject.toml` + CI | 配置 `pytest-cov`，在 CI 中输出覆盖率；目标: ≥85% |
| 1.3 | Ruff lint 检查 | CI | 在 CI 中添加 `ruff check` + `ruff format --check` 步骤 |
| 1.4 | Importer 边界测试补充 | `test_importers.py` | 空文件、编码错误、超大行、重复 ID 等边界 case |
| 1.5 | Validator 边界测试补充 | `test_validators.py` | 嵌套 schema 错误消息、多错误聚合、路径不存在等 |

**依赖**: Stage 0 完成后执行。

---

### Stage 2: CLI 功能完善

> 补齐规范中定义但 CLI 尚未实现的功能。

| # | 任务 | 子命令 | 说明 |
|---|------|--------|------|
| 2.1 | `llmindex init` | 新增 | 交互式生成 `llmindex.yaml` 配置文件（站点名、URL、语言、主题）；替代手动 `--site`/`--url` 参数 |
| 2.2 | 支持 YAML config | `generate` 改进 | 新增 `--config llmindex.yaml` 选项，从 YAML 读取 site/url/language/topics，与命令行参数合并 |
| 2.3 | `llmindex verify` | 新增 | 域名验证子命令: (a) `verify dns` — 输出应设置的 TXT 记录值; (b) `verify http` — 输出应放置的验证文件内容; (c) `verify check` — 检查验证是否通过。实际 DNS/HTTP 查询使用 `dns.resolver` / `httpx` |
| 2.4 | `llmindex status` | 新增 | 读取已生成的 manifest，展示摘要（站点名、端点数、上次更新、验证状态等） |
| 2.5 | `generate` 改进: 无产品模式 | `generate` | 支持仅生成 manifest + pages（不要求 `--input-*`），适合非电商站点（SaaS、博客等） |
| 2.6 | `generate` 改进: 自定义页面模板 | `generate` | `--templates-dir` 选项，允许用户提供自定义 Jinja2 模板替代硬编码的 policies/faq/about 页面 |
| 2.7 | `validate` 改进: URL 可达性检查 | `validate` | `--check-urls` flag，使用 HEAD 请求验证 endpoints 中的 URL 是否可访问 |

**优先级排序**: 2.1 → 2.2 → 2.5 → 2.3 → 2.4 → 2.6 → 2.7

**依赖**:
- 2.1 和 2.2 无依赖，可立即开始
- 2.3 需要新增 `dns.resolver` + `httpx` 依赖
- 2.6 需要新增 `jinja2` 依赖

---

### Stage 3: 规范文档正式化

> 将 spec 从 Draft 升级为正式 v0.1 发布状态。

| # | 任务 | 文件 | 说明 |
|---|------|------|------|
| 3.1 | Spec 正式化 | `spec/spec.md` | 移除 Draft 标记，添加 Changelog 节，添加 IANA considerations，补充 Security Considerations |
| 3.2 | 中文版规范 | `spec/spec.zh.md` (新建) | 从 `spec/spec.md` 翻译完整中文版，替代旧的 `llmindex_spec_v0_1.md` |
| 3.3 | JSON Schema 文档化 | `spec/schemas/` | 在 schema 中添加 `description` 和 `$comment` 字段，生成 schema 参考文档 |
| 3.4 | Feed Schema 独立文件 | `spec/schemas/product-line-0.1.schema.json` (新建) | 将 `product_line` 定义从主 schema 的 `$defs` 提取为独立 schema，便于 feed-only 验证 |
| 3.5 | 更多 test vectors | `spec/test-vectors/` | 补充: `invalid-extra-fields.json`, `invalid-http-url.json`, `valid-minimal.json`, `valid-with-verify.json` |
| 3.6 | 更多 industry examples | `spec/examples/` | 补充: `blog/`, `restaurant/`, `marketplace/` 行业示例 |
| 3.7 | docs site 更新 | `docs/index.html` | 同步最新规范内容和 CLI 用法到文档站 |

**优先级排序**: 3.1 → 3.2 → 3.4 → 3.5 → 3.3 → 3.6 → 3.7

**依赖**:
- 3.1 可立即开始（与 Stage 2 并行）
- 3.4 完成后需更新 validators.py 的 feed 验证逻辑

---

### Stage 4: 路线图规划 (v0.2+)

> 产出正式路线图文档，指导后续开发方向。

| # | 任务 | 文件 | 说明 |
|---|------|------|------|
| 4.1 | 路线图文档 | `ROADMAP.md` (新建) | v0.1.x (当前) → v0.2 → v1.0 的功能规划，含时间线和优先级 |
| 4.2 | 清理旧文档 | 多个文件 | 归档/删除 `llmindex_spec_v0_1.md`（被 3.2 替代）、`llmindex_execution_plan.csv`（已过时）、`llmindex_business_roadmap.md`（私有化或归档） |

---

## 执行顺序与并行策略

```
Stage 0 (Hotfix)                          ← 立即执行
    │
    ├── Stage 1 (质量加固) ──────────┐
    │   1.1 CLI 集成测试              │
    │   1.2 覆盖率                    │    可与 Stage 3 并行
    │   1.3 Lint                      │
    │   1.4-1.5 边界测试              │
    │                                 │
    ├── Stage 3 (规范正式化) ─────────┤
    │   3.1 Spec 正式化               │    可与 Stage 1 并行
    │   3.2 中文版                    │
    │   3.4-3.5 Schema + Vectors      │
    │                                 │
    ▼                                 │
Stage 2 (CLI 功能)                    │
    2.1 init                          │
    2.2 YAML config                   │
    2.5 无产品模式                     │
    2.3 verify                        │    ← 依赖 Stage 1 的测试基础
    2.4 status                        │
    2.6-2.7 模板/URL 检查             │
    │                                 │
    ▼                                 ▼
Stage 4 (路线图)                      ← 所有 Stage 完成后
    4.1 ROADMAP.md
    4.2 清理旧文档
```

---

## 建议的会话分配

| 会话 | Stage | 任务量 | 说明 |
|------|-------|--------|------|
| **会话 A** | 0 + 1 | 小 | Hotfix + 质量加固（测试为主，不改业务逻辑） |
| **会话 B** | 3 | 中 | 规范文档正式化（文档密集，可与 A 并行） |
| **会话 C** | 2.1-2.5 | 大 | CLI 核心功能（init/yaml/verify/status/无产品模式） |
| **会话 D** | 2.6-2.7 + 4 | 中 | CLI 增强 + 路线图 |

**或者合并为 2 个大会话**:
- **会话 1**: Stage 0 + 1 + 3（修复 + 加固 + 规范）
- **会话 2**: Stage 2 + 4（功能开发 + 路线图）

---

## v0.2 路线图预览

> 供 Stage 4.1 的 ROADMAP.md 参考。

### v0.1.x (当前维护)
- CLI 功能完善 (init/verify/status/yaml-config)
- 规范正式化
- 质量加固

### v0.2 (下一个 minor)
- **多语言 manifest**: `language` 字段支持数组，多语言端点
- **Spec 扩展**: `access_control` 字段（哪些 AI 可访问、速率限制建议）
- **签名实现**: EdDSA JWS 签名生成 + 验证（spec 已定义但未实现）
- **增量更新**: `updated_at` 对比 + 差异通知
- **CLI watch 模式**: 监控源数据变化，自动重新生成

### v1.0 (稳定版)
- Backward compatibility 保证
- 完整的 conformance test suite
- 官方 validator service (SaaS)
- SDK: Python + TypeScript + Go

---

## 新增依赖一览

| 依赖 | Stage | 用途 |
|------|-------|------|
| `pyyaml>=6.0` | 2.2 | YAML 配置文件解析 |
| `dnspython>=2.6` | 2.3 | DNS TXT 记录查询 |
| `httpx>=0.27` | 2.3, 2.7 | HTTP HEAD 请求（验证 + URL 检查） |
| `jinja2>=3.1` | 2.6 | 自定义页面模板 |

建议将非核心依赖设为 optional extras:
```toml
[project.optional-dependencies]
verify = ["dnspython>=2.6", "httpx>=0.27"]
templates = ["jinja2>=3.1"]
all = ["dnspython>=2.6", "httpx>=0.27", "jinja2>=3.1"]
```
