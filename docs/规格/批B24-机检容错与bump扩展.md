# 规格 · 批 B24：机检解析器格式容错 + bump 脚本 setup_version 扩展

- 版本：v1.0（2026-08-24）
- 前置依赖：B23 已合入。
- 依据：test2-4 实测观察 010（check_outline.py 四项格式容错不足）+ 观察 008 待办（bump 脚本 --setup-version）。

---

## 一、现状事实（施工前复核）

1. `python skills/moshu-build/scripts/check_outline.py --project otherMaterials/testProject/test2-4` 产出（已修格式后）`{"ok": true, "blocking": [], "candidate": ["暗线每卷至少推进一格…"]}`——当前全绿是因为 AI 会话内修了大纲格式适配解析器。
2. **首跑曾出的 1 blocking + 3 candidate 全是解析器格式容错问题**（真实数据正确但解析器读不到）：
   - blocking：四阶段占比行尾注"（合计 100%）"的 100 被 % 正则误捕（100+100=200）
   - candidate：升级台阶"4 大阶段 × 100 万字"的中文量词"大阶段"导致档数×卷幅正则不匹配
   - candidate：终局底牌条目以 `- ` bullet 开头被过滤器剔除
   - candidate：势力场势力名带"（描述）"后缀导致互引名字匹配不到完整名
3. `scripts/bump-agents-version.py` 不含 `--setup-version` 参数——setup_skill_version 变化时 6 处仍靠手工（观察 008：bump 1.5.0→1.5.1 漏了 deploy.py 第 6 处）。

## 二、设计总纲

### 产出①：check_outline.py 四项格式容错

| # | 问题 | 修法 | 原则 |
|---|---|---|---|
| 1 | % 正则误捕注释 | 占比提取时**排除括号内文本**（`（合计 100%）`→只取表格数据行的 % 值）——用 `re.sub(r'（[^）]*）', '', line)` 预处理后再 findall | 宁可漏拦不可误伤 |
| 2 | 中文量词阻断数字对 | 升级台阶正则放宽——容忍数字与"×"之间夹中文（`r'(\d+)\s*[^\d×]+\s*×\s*(\d+)'` 或等价），解析不到时降 candidate 不升 blocking | 同上 |
| 3 | bullet 前缀被剔除 | 终局底牌条目解析容忍 `- ` 前缀——`line.lstrip('- ').strip()` 预处理 | 同上 |
| 4 | 括号后缀影响互引匹配 | 势力场互引匹配时去除势力名的括号后缀——`name.split('（')[0].strip()` 后再比对 | 同上 |

**通用原则**：所有解析增强方向为"更宽容地读入正确格式的变体"，非"更严格地拒绝"——解析不到的一律降 candidate（提示人工核）而非 blocking。

### 产出②：bump-agents-version.py 加 --setup-version

新增可选参数 `--setup-version <旧版本> <新版本>`（与 agents_version 独立）：

```
python scripts/bump-agents-version.py 34 --setup-version 1.5.1 1.6.0
```

setup_version 覆盖 **6 处**：
1. `skills/moshu-setup/SKILL.md` frontmatter `version:`
2. `scripts/current-contract.json` `setup_skill_version`
3. `skills/moshu-setup/SKILL.md` 哨兵样例 `setup_skill_version: X`
4. `skills/moshu-setup/UPGRADING.md` 版本头 `setup_skill_version: X`
5. `skills/moshu-setup/references/deploy-manual.md` 两处
6. `skills/moshu-setup/scripts/deploy.py` `DEFAULT_SETUP_VERSION = 'X'` + CLI 帮助 `--setup-version X`

与 agents_version 同一套 diff 预览→--confirm→守卫→回滚 逻辑。agents_version 与 setup_version 可独立使用（只 bump 其一合法）。

## 三、文件级改动清单

1. `skills/moshu-build/scripts/check_outline.py`：四项容错增强（各 3-5 行）
2. `scripts/test-check-outline.py`：新增 fixture 4 组（注释%不误捕/量词容忍/bullet 前缀容忍/括号后缀去除）
3. `scripts/bump-agents-version.py`：加 --setup-version 参数 + 6 处覆盖 + diff/confirm/守卫/回滚
4. `scripts/test-bump-agents-version.py`：新增 setup_version bump 用例（含 deploy.py 常量+六处全替换+回滚测试）
5. `scripts/README.md` 索引同步（bump 脚本用法加 --setup-version 示例）

## 四、禁止事项

1. 容错增强**不降低既有断言的检测精度**——只增加格式变体的读入能力，不放过真实违规
2. bump 脚本 setup_version 与 agents_version **独立轨**——允许只 bump 其一
3. 守卫失败回滚必须覆盖两类版本（agents 或 setup 任一改动失败→全部回滚）
4. 机检解析不到的一律 candidate（不升 blocking）——宪法 §2.7 候选永不拦截

## 五、验收命令

```bash
# 产出①：容错——用 test2-4 已修格式的大纲验证（全绿不受影响）
python skills/moshu-build/scripts/check_outline.py --project otherMaterials/testProject/test2-4
# 期望 0 blocking（现有全绿不受影响）

# 容错——构造带"（合计 100%）"注释/bullet/量词/括号后缀的 fixture，验证不再误报
python scripts/test-check-outline.py
# 全绿（含 4 组新 fixture）

# 产出②：bump --setup-version
python scripts/bump-agents-version.py 33 --setup-version 1.5.1 1.6.0
# 预览：agents 无 diff（当前 33→33），setup 6 处列出
python scripts/bump-agents-version.py 33 --setup-version 1.5.1 1.6.0 --confirm
# 执行替换+守卫→守卫红（版本不匹配）→自动回滚→退出非零
python scripts/test-bump-agents-version.py
# 全绿（含新 setup_version 用例）

# 全量守卫
bash scripts/static-check.sh && bash scripts/check-doc-budget.sh && bash scripts/check-shared-files.sh
```

## 六、提交规范

`fix(scripts): check_outline.py 四项格式容错（括号注释%/中文量词/bullet 前缀/括号后缀）+ bump-agents-version.py 加 --setup-version 六处覆盖（观察 010+008 待办；B24）`
