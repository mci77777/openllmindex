# OpenLLMIndex 核心库 — 开发编排计划

> 本文档规划「核心库功能完善」「规范文档正式化」「质量加固」「路线图」四个方向的任务分解与执行顺序。
> 所有任务在 `openllmindex` 仓库执行。

---

## 当前状态摘要

> 最后更新: 2026-02-22

| 模块 | 状态 | 备注 |
|------|------|------|
| CLI (generate/validate/init/verify/status) | ✅ 完整 | Stage 1+2 全部完成 |
| Importers (CSV/JSON/Shopify/YAML) | ✅ 完整 | 含 YAML config 导入 |
| Validators | ✅ 完整 | 含 URL 可达性检查 (`--check-urls`) |
| Spec (spec.md) | ✅ 正式化 | 已移除 Draft 标记，含 Changelog/Security |
| Spec (spec.zh.md) | ✅ 完整 | 中文版规范已创建 |
| JSON Schema (llmindex-0.1) | ✅ 完整 | 含 description/$comment 注释 |
| Feed Schema (product-line-0.1) | ✅ 完整 | 独立 schema 文件 |
| Tests | ✅ 100+ cases | CLI 集成测试 + 边界测试，覆盖率 ≥85% |
| PyPI (openllmindex) | ✅ 已发布 | v0.1.0 @ pypi.org/project/openllmindex |
| npm (@llmindex/schema) | ✅ 已发布 | v0.1.0 @ npmjs.com/package/@llmindex/schema |
| CI/CD | ✅ 完整 | tag 推送自动触发 PyPI + npm 双包发布 |
| ROADMAP.md | ✅ 完整 | v0.1.x → v0.2 → v1.0 |
| demo.py | ✅ 修复 | 路径 `cli/` → `llmindex/` 已更新 |
| docs site | 🔄 部分 | 内容可能滞后规范 |
| Industry examples | 🔄 部分 | ecommerce/local-business/saas 已有，待补 blog/restaurant/marketplace |

---

## 执行阶段

### Stage 0: 紧急修复 (Hotfix) ✅ 完成

> 优先级最高，修复已知 broken 的代码。

| # | 任务 | 文件 | 状态 |
|---|------|------|------|
| 0.1 | 修复 demo.py 路径 bug | `examples/demo.py:38` | ✅ commit `4bb8d8d` |
| 0.2 | commit portal 原型 | `portal-prototype/`, `design-system/` | ✅ commit `4bb8d8d` |

---

### Stage 1: 质量加固 ✅ 完成

> 在添加新功能之前，先巩固现有代码的测试覆盖和质量。

| # | 任务 | 范围 | 状态 |
|---|------|------|------|
| 1.1 | CLI 集成测试 | `llmindex/tests/test_cli.py` | ✅ commit `0abbc7a` |
| 1.2 | 测试覆盖率报告 | `pyproject.toml` + CI | ✅ ≥85% 配置完成 |
| 1.3 | Ruff lint 检查 | CI | ✅ commit `c584f9a` |
| 1.4 | Importer 边界测试补充 | `test_importers.py` | ✅ commit `0abbc7a` |
| 1.5 | Validator 边界测试补充 | `test_validators.py` | ✅ commit `0abbc7a` |

---

### Stage 2: CLI 功能完善 ✅ 完成

> 补齐规范中定义但 CLI 尚未实现的功能。

| # | 任务 | 子命令 | 状态 |
|---|------|--------|------|
| 2.1 | `llmindex init` | 新增 | ✅ commit `0abbc7a` |
| 2.2 | 支持 YAML config | `generate` 改进 | ✅ commit `0abbc7a` |
| 2.3 | `llmindex verify` | 新增 | ✅ commit `0abbc7a` |
| 2.4 | `llmindex status` | 新增 | ✅ commit `0abbc7a` |
| 2.5 | `generate` 改进: 无产品模式 | `generate` | ✅ commit `0abbc7a` |
| 2.6 | `generate` 改进: 自定义页面模板 | `generate` | ✅ commit `0abbc7a` |
| 2.7 | `validate` 改进: URL 可达性检查 | `validate` | ✅ commit `0abbc7a` |

---

### Stage 3: 规范文档正式化 🔄 部分完成

> 将 spec 从 Draft 升级为正式 v0.1 发布状态。

| # | 任务 | 文件 | 状态 |
|---|------|------|------|
| 3.1 | Spec 正式化 | `spec/spec.md` | ✅ commit `0abbc7a` |
| 3.2 | 中文版规范 | `spec/spec.zh.md` | ✅ commit `0abbc7a` |
| 3.3 | JSON Schema 文档化 | `spec/schemas/` | ✅ 已完成（description/$comment 字段齐全）|
| 3.4 | Feed Schema 独立文件 | `spec/schemas/product-line-0.1.schema.json` | ✅ 已存在并发布至 npm |
| 3.5 | 更多 test vectors | `spec/test-vectors/` | ✅ 已完成（8 个 vector 全部存在）|
| 3.6 | 更多 industry examples | `spec/examples/` | 🔄 ecommerce/local-business/saas 已有，待补 blog/restaurant/marketplace |
| 3.7 | docs site 更新 | `docs/index.html` | 🔄 内容可能滞后 |

---

### Stage 4: 路线图规划 (v0.2+) ✅ 完成

> 产出正式路线图文档，指导后续开发方向。

| # | 任务 | 文件 | 状态 |
|---|------|------|------|
| 4.1 | 路线图文档 | `ROADMAP.md` | ✅ 已创建 |
| 4.2 | 清理旧文档 | 多个文件 | ✅ 旧文档已归档至 `docs/archive/` |

---

### Stage 5: 打包与发布 ✅ 完成 (新增)

> CI/CD 完整建立，双包发布流程正常。

| # | 任务 | 状态 |
|---|------|------|
| 5.1 | 重命名包 `llmindex` → `openllmindex`（避免 PyPI 名称冲突） | ✅ commit `12a36dc` |
| 5.2 | PyPI 发布 `openllmindex 0.1.0` | ✅ https://pypi.org/project/openllmindex/ |
| 5.3 | npm 发布 `@llmindex/schema@0.1.0` | ✅ https://www.npmjs.com/package/@llmindex/schema |
| 5.4 | CI/CD: tag 推送自动发布 (`v*` tag → test → publish) | ✅ commit `55d8742` |
| 5.5 | 版本一致性检查 (pyproject.toml == package.json == git tag) | ✅ commit `55d8742` |
| 5.6 | NPM_TOKEN 更新为 granular bypass-2FA token | ✅ GitHub Secret 已更新 |

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
