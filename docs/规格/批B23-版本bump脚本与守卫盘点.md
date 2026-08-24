# 规格 · 批 B23：版本 bump 确定性脚本 + 守卫有效性盘点

- 版本：v1.0（2026-08-24，作者裁决"全都修复"+开发标准落地）
- 前置依赖：无。
- 依据：观察 024（agents_version 版本字面量五层散射，CI 连续三笔修复的教训）+ 观察 025 P2/P4。

---

## 一、现状事实（施工前复核）

1. 全仓 agents_version=33 的字面量分布（已穷举核实）：
   - `scripts/current-contract.json`（agents_version 字段，数字）
   - 9 个 `skills/**/SKILL.md`（Spawn 版本提示段，反引号 `` `33` `` + 无反引号 `33 时额外`）
   - `skills/moshu-setup/SKILL.md`（部署判定门，反引号 `` `33` ``）
   - `skills/moshu-setup/references/templates/hooks/session-start.sh`（比较值 `-lt 33` / `-gt 33` + 措辞 `低于 v33` / `高于本 hook 支持的 v33`）
   - `skills/moshu-setup/references/deploy-manual.md`（三处反引号 `` `33` ``）
   - `skills/moshu-setup/UPGRADING.md`（版本头 `agents_version: 33` + 升级步骤行 + 历史条目）
2. 无 bump 脚本——每次升 agents_version 为手工 grep+replace，已证明漏（观察 024 五层散射清单）。
3. 守卫清单：`ls scripts/check-*` + `ls scripts/test-*` 共 55 个，未做过零命中盘点。

## 二、设计总纲

### 产出①：`scripts/bump-agents-version.py`

确定性脚本，替代一切手工 agents_version bump。

**输入**：`python scripts/bump-agents-version.py <新版本号>`
**行为**：
1. 读 `scripts/current-contract.json` 取当前 agents_version
2. 全仓 grep 六类文件中的当前版本字面量（六类=SKILL.md×2 格式/current-contract.json/session-start.sh/deploy-manual.md/UPGRADING.md 版本头——**不含 UPGRADING 历史条目**）
3. 列出 diff 预览（文件:行号:旧值→新值）
4. `--confirm` 参数：确认后执行替换
5. 替换后自动跑三个守卫：`check-current-skill-contracts.sh` + `check-moshu-setup-deployment.sh` + `check-agents-version-sync.py`
6. 守卫全绿 → 提示"bump 完成，可提交"
7. 守卫有红 → 回滚所有替换（临时备份），报错退出

**不动的**：UPGRADING.md 历史条目（v28→v29 变更等）只改版本头和升级步骤行。

**CLI**：
```
python scripts/bump-agents-version.py 34           # 预览 diff
python scripts/bump-agents-version.py 34 --confirm  # 执行替换+守卫
```

### 产出②：守卫有效性盘点脚本 `scripts/audit-guards.py`

一次性工具（用完可删或留作年度审计）。

**行为**：
1. 列出所有 check-*/test-* 脚本
2. 对每个脚本 grep `.github/workflows/cross-platform.yml` 是否登记
3. 输出报告：`脚本名 | 是否在 CI | 最近修改日期 | 建议（保留/候选下线/未接入）`
4. **不做任何修改**——只出报告，作者裁决

### 产出③：开发标准落线

`docs/开发标准.md` 已由规划侧产出（本规格随批入库）——施工方不改内容，只确认入库。

## 三、文件级改动清单

1. **新建** `scripts/bump-agents-version.py`（~120 行）：
   - 读 current-contract 取当前值
   - 六类文件 grep（正则覆盖反引号/无反引号/JSON 数字/shell 比较值四种格式）
   - diff 预览 + --confirm + 替换 + 三守卫 + 失败回滚
   - 排除 UPGRADING 历史条目（grep 上下文排除 `变更` 关键词的行）
2. **新建** `scripts/test-bump-agents-version.py`（正式回归，~60 行）：
   - 守护对象声明
   - fixture：临时仓（tempfile）→ 设 current-contract=33 → bump 到 34 → 断言六类文件全替换 → 断言历史条目未动 → 回滚测试
3. **新建** `scripts/audit-guards.py`（~50 行，一次性工具，不进 CI）
4. **CI 三处同步**：bump 脚本的回归测试 `test-bump-agents-version.py` 进 CI + CONTRIBUTING + scripts/README
5. `docs/开发标准.md` 入库
6. `docs/施工日志.md` B23 条目
7. `docs/规格/批B23-*.md` 随批

## 四、禁止事项

1. bump 脚本**不修改 UPGRADING.md 历史条目**（v28→v29 等变更记录不动）
2. bump 脚本**不修改 marketplace.json / SKILL.md frontmatter version**（那是插件版本，独立轨——本脚本只管 agents_version）
3. 守卫失败时**必须回滚**（不留半改状态）
4. audit-guards.py 只出报告不做修改
5. 开发标准内容**施工方不改**（规划侧产出物，只入库）

## 五、验收命令

```bash
python scripts/bump-agents-version.py 33            # 当前值=33，无 diff，退出 0
python scripts/bump-agents-version.py 34            # 预览 diff（六类文件列出），退出 0
python scripts/test-bump-agents-version.py          # 全绿
python scripts/audit-guards.py                      # 输出报告（退出 0）
bash scripts/static-check.sh                        # 全绿（不影响现有守卫）
ls docs/开发标准.md                                  # 存在
grep -c "bump-agents-version" .github/workflows/cross-platform.yml CONTRIBUTING.md scripts/README.md  # 各 ≥1
```

人为破坏自测：把 current-contract 改为 32 → bump 到 33 → 六类文件中残留的 32 全替换 → 守卫绿。

## 六、提交规范

`feat(scripts): 版本 bump 确定性脚本 bump-agents-version.py（六类文件 grep+diff 预览+--confirm+三守卫+失败回滚）+守卫有效性盘点 audit-guards.py+CI 三处同步；开发标准 docs/开发标准.md 入库（观察 024/025 P2+P4；B23）`
