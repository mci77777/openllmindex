# ROADMAP

## v0.1.x (当前)

- CLI 功能完善（init / verify / status / YAML config / templates / URL check）
- 规范正式化（spec 文档与示例持续对齐）
- 质量加固（更多测试覆盖、lint/CI 稳定性、错误信息与 DX 优化）

## v0.2 (下一个 minor)

- 多语言 manifest（多语言 endpoints/feeds 元数据与选择策略）
- `access_control` 字段（声明访问控制、robots/AI policy、认证方式提示）
- EdDSA JWS 签名（签名生成与验证、key discovery、kid 约定）
- 增量更新（updated_at + feed 增量策略、diff/patch 机制探索）
- CLI watch 模式（监听输入数据变化、自动重建 artifacts）

## v1.0 (稳定版)

- 向后兼容保证（semver + 兼容策略与迁移指南）
- conformance test suite（标准化测试向量与实现一致性验证）
- 官方 validator service（在线校验与诊断报告）
- Python/TS/Go SDK（读取/生成/验证/签名的官方库）

