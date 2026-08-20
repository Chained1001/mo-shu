# 审计-V3：逐 skill 审计与整改总入口

- 版本：v1.0（2026-08-21）
- 发起：作者明确发起（V2 收官后规划冻结已解除，见 `AGENTS.md` 头部说明）。
- 定位：**V2 收官后的第一次全量体检**。V2 建成的能力（追踪 schema v5 / 候选机检 / 审查工单 / 模板纪律 / 场景 eval）已逐批验收通过；本轮不新增能力，只查「已建成的能力是否真的在流程里接线、文档与代码是否仍然一致、守卫是否有盲区」。
- 与既有文档的关系：
  - `docs/执行总纲V2.md`（术语表 §三、不学清单附录 B、雷区附录 D）是**判定依据**，本轮不修订它；
  - `docs/规格-V2/`（逐批规格 + 施工日志 + 审核记录）是**历史依据**，只读引用，不修改；
  - `docs/归档/**` 零接触。

---

## 1. 审计范围与状态总表

| # | skill | 审计状态 | 整改状态 | 记录文件 |
|---|---|---|---|---|
| 1 | moshu-write | 已完成 | 已整改（W1/W2/W3/W5，W4 随 G5） | [审计-moshu-write.md](审计-moshu-write.md) |
| 2 | moshu-setup | 已完成 | 已整改（PM1/PM2/PM3/PM6/PM9；PM4① ②已做、③待作者确认） | [审计-moshu-setup.md](审计-moshu-setup.md) |
| 3 | moshu-review | 已完成 | 已整改（RB1/RB2/RM1/RM2/RM3/RM4/RC1） | [审计-moshu-review.md](审计-moshu-review.md) |
| 4 | moshu-import | 已完成 | 已整改（IM1-IM6） | [审计-moshu-import.md](审计-moshu-import.md) |
| 5 | moshu-analyze | 已完成 | 已整改（AM1/AM2/AM3/AM4） | [审计-moshu-analyze.md](审计-moshu-analyze.md) |
| 6 | moshu-scan | 已完成 | 已整改（SM1/SM2/SM3/SM5/SC2/SC4/SC5；SM4 联合契约用例部分落地） | [审计-moshu-scan.md](审计-moshu-scan.md) |
| 7 | moshu-deslop | 已完成 | 已整改（DM1/DM2/DM3/DC1/DC2） | [审计-moshu-deslop.md](审计-moshu-deslop.md) |
| 8 | moshu-style | 已完成 | 已整改（S1/S2/S5→agents_version 30；S3 见跨 skill G2） | [审计-moshu-style.md](审计-moshu-style.md) |
| 9 | moshu | 已完成 | 已整改（M1/M2/M4/M5/C2/C3） | [审计-moshu.md](审计-moshu.md) |
| 10 | moshu-cdp | 已完成 | 已整改（N1/N2/N3） | [审计-moshu-cdp.md](审计-moshu-cdp.md) |
| — | 跨 skill / 仓库级 | 已完成 | 已整改（G1/G2/G4/G5/G7 + **施工中新发现：hook schema v4→v5 阻断级缺陷**） | [审计-跨skill与仓库级.md](审计-跨skill与仓库级.md) |
| — | **整改总计划** | 施工完毕 | **A→H 全部执行完毕，终检 39/40 绿（1 项为已知 Windows chmod 平台限制）** | [整改总计划.md](整改总计划.md) |

> **已闭环（2026-08-21 第二轮）**：PM4③ 欠账门测试已补并随部署检查绿（正向拦截 + `去味:跳过` 豁免双向断言）；SM4 联合契约用例已落地（qidian/qimao 真实 renderMarkdown ↔ adapt，test-scan-analyze 13/13）；三项待裁定按推荐方案落地——AC1 Stage 0 骨架改 `partial` + 恢复机制补概要核对、IC1 存档承诺文档诚实化、AC5 术语表补"泛指对标作品可用『对标书』"边界。
> **已闭环（2026-08-21）**：PM4③ 欠账门测试已补（正向拦截 + `去味:跳过` 豁免双向断言）；SM4 联合契约用例已落地（qidian/qimao 真实 renderMarkdown ↔ adapt，13/13）；三项待裁定按推荐方案落地；**C7 勘误已获作者授权落档**（`docs/规格-V2/审核记录.md` 追加"批9 追加勘误"节，欠账门纳入原裁决范围）。
> **待作者处理**：git 提交（作者已授权，按主题分 4 个提交执行）。

## 1.1 审计方式与复核纪律

- 10 个 skill 中 **moshu-write / moshu-style / 跨 skill 三份由本人直接审计**，其余 7 个由 5 个并行子代理深审后**由本人独立复核关键结论**（每条标注 ✅本人复核成立）。
- 复核已产生 **1 条推翻**（`scripts/README.md:15`「64 组」经真跑 `check-shared-files.sh` 证实文档正确，子代理复算口径有误）与 **2 处定性修正**（moshu 的 Fallback 枚举权威范围、moshu-style 的"批 2 是否漏掉"措辞）——这三条已分别写进对应报告，作为"不信任转述"纪律的执行证据。

## 2. 分级定义（三级，与总纲「候选永不拦截」精神一致）

| 级别 | 判据 | 处置 |
|---|---|---|
| **阻断级** | 违反规格既有约束 / 破坏已验收契约 / 脚本失效 / 副本字节不一致 | 必修，优先于一切 |
| **需修级** | 真实缺口或文档-代码不一致：能力已建成但流程未接线、可数断言与实测不符、跨 skill 措辞冲突 | 建议修，作者勾选 |
| **候选级** | 呈报性发现：覆盖不对称、预算余量、虚化断言、可读性与噪音 | 只记录，作者决定是否动 |

## 3. 审计维度（每个 skill 固定八条，缺一条要说明为什么）

1. **引用图**：死链（引用不存在的文件）与孤儿（存在但无人引用）。
2. **流程闭环**：SKILL.md 场景路由 → references 工作流 → 产物落盘 → 状态提交，是否每条路径都能走完。
3. **守卫与契约覆盖**：`scripts/behavior-contracts.json` / `doc-budget.json` / `shared-assets.json` / `current-contract.json` / `README.md` 的 check-*·test-* 清单；明确写出"改了不会被任何守卫发现"的盲区。
4. **术语与数字断言**：按总纲 §三术语表查禁用别称；逐条数所有可数声明（这是最易过期的一类）。
5. **脚本接入点**：确定性脚本在流程文档里有没有真实调用点（**接线缺口**是本轮最主要的问题类型）。
6. **跨 skill 一致性**：共享副本字节一致、降级措辞一致、产物契约两侧对齐。
7. **测试与 eval 覆盖**：正式回归覆盖了什么、漏了什么；eval 断言是否存在"永远为真"的虚化项。
8. **版本口径**：SKILL.md frontmatter version / `.claude-plugin/marketplace.json` / `skills/moshu/VERSION` / `agents_version` 四轨。

## 4. 记录文件格式（每 skill 一份，末尾必须有整改计划表）

```markdown
# {skill} 审计报告
## 一、结论
## 二、阻断级
## 三、需修级
## 四、候选级
## 五、覆盖矩阵
## 六、实测记录
## 七、整改计划（编号 / 级别 / 修法 / 改动量 / 验收命令 / 依赖）
```

每条发现必须写：**现象 / 证据（`文件:行号`，须真实核对）/ 影响 / 建议修法（最小改动）/ 预估改动量**。
纪律（沿用 `AGENTS.md` §7）：区分「代码事实」与「（推断）」；拿不准标「存疑」；不臆造行号；不为凑数报无意义发现。

## 5. 环境须知（本轮实测环境）

- `bash` 可用（Git Bash `MINGW64`）；**无 `python3`**，需临时 shim（`.tmp/bin/python3` → `exec python "$@"`）后 `.sh` 守卫方可全量复跑——与 `docs/规格-V2/README.md` §7 的 Windows 惯例一致。
- 临时产物一律 `.tmp/`，用完即删（`AGENTS.md` §1.4）。
- 基线：整改前跑一次全量守卫存档，整改后逐项复跑对比，**禁止改断言变绿**。

## 6. 红线（与 `AGENTS.md` 一致，审计与整改全程有效）

git 只读默认——**任何 commit/push 须作者明确语言授权**；参考项目 `otherMaterials/referProject/**` 绝对只读；`docs/归档/**` 零接触；一批一提交；候选永不拦截；不学清单 14 条勿静默引入（数据库后端、RAG、Dashboard 常驻服务化、npx 分发改造、拦截式 hook 门禁等）。
