# moshu-setup 技能审计报告 v1

> 依据 `docs/审计法.md` v1.6 六步 SOP；对 `skills/moshu-setup/` 全量（SKILL.md / scripts×2 / references 全部 / templates 全部 26 文件）。
> 版本快照：agents_version 34 · setup_skill_version 1.5.1 · 包版本 2.3.6（`skills/moshu/VERSION` 实测）。
> 方法注记：setup 为基建技能，Step 2c 填充测试以**行为实测替代**（T1-T5 真实部署场景，临时目录已删）；本文只查不改，修复走后续规格批次。

---

## 一、基线（Step 1）【事实】

- 18 个 Python 回归测试全绿（含 test_deploy / test-bump-agents-version）。
- 守卫：agents-version-sync 34 一致 ✓ / reference-closure 114 ✓ / capability-wiring 13/35 ✓ / story-numbers ✓ / check-shared-files 71 组 0 失配 ✓ / current-skill-contracts（.py 直跑）✓。
- `check-current-skill-contracts.sh` 在本机 shell 直跑报 SyntaxError——Windows 下 .sh wrapper 形态误用，等价 .py 检查绿，非真红（自我推翻 §九.2）。

## 二、结构与引用（Step 2a/2b/2d）

**体量与冷热分离**：SKILL.md 98 行（热路径，脚本优先+冷路径指针）→ deploy-manual.md 108 行（兜底）→ UPGRADING.md 131 行（版本权威）。分离良好，无超预算。

**安全面**：部署面无 LLM/联网依赖；deploy.py/merge-claude-settings.py 纯确定性；无秘密泄露；临时实测全部走 `/.tmp/tests/setup-audit/` 用完即删。

**单源判定（§5.1 适用性）**：templates 26 文件（8 agents + 10 hooks 相关 + 4 rules + CLAUDE.md.tmpl + settings-hooks.json）全仓查重**均为单源**——§5.1 全量副本登记不适用，非违例【事实】。

**热消费抽检（2b）**：SKILL.md 三处版本字面（:23/:24/:25 阈值、:50 sentinel 模板）全为 34 ✓；但冷路径与用户文档存在阈值过期（见 §七 需修 1）与计数过期（需修 3）。

**开发标准合规（2d）**：SKILL.md frontmatter 合规 ✓；交互模态三规则合规（部署位置/重部署确认封闭问→AskUserQuestion，CONFLICT 处置→AskUserQuestion，参考包缺失→停止报告）✓；脚本纪律合规（deploy.py exit 0/1/2 分层、fatal 给手动修复步骤；merge helper 原子写+幂等；读失败带分类报错）✓；版本管理：UPGRADING.md 权威在位 ✓，bump 覆盖面存在盲区（需修 1）。

## 三、行为实测（Step 2c 基建版，替代填充测试）

| 场景 | 结果 | 判定 |
|---|---|---|
| T1 全新部署+verify | deploy exit 0：hooks 8+lib / rules 4 / agents 8 / agent-references 34 项 / CLAUDE.md 生成 / settings 合并 JSON 有效 / sentinel 6 字段；verify **7 项全 PASS**，exit 0 | ✅ |
| T2 幂等性 | settings 字节稳定 ✓；sentinel 变化=时间戳预期；**CLAUDE.md 首次重部署字节变化**（节间 1→2 空行），第 3/4 次部署 md5 稳定=收敛 | ⚠️ 候选 4 |
| T3 CLAUDE.md section 合并 | 旧版「Skill 路由表」被模板覆盖 ✓；「我的自定义节」保留 ✓；5 个模板节齐全 ✓；标题占位符替换 ✓ | ✅ |
| T4 纯自定义 CLAUDE.md（无 `##`） | 报 CONFLICT 不覆盖 ✓ 用户文件零接触 ✓（铁律实测成立）；但 sentinel 照写、deploy exit 0、verify 全绿（verify 检查面不含 CLAUDE.md） | ⚠️ 候选 6 |
| T5 降级门禁 | sentinel 改 99 后 deploy → `exit 1`「禁止降级覆盖」 | ✅ |

## 四、机制链（Step 3a）

- **链 1 安装→开窗→setup→deploy→verify→sentinel→session-start**：闭合。SKILL.md Phase 1 版本展示（读 `skills/moshu/VERSION`，实测存在=2.3.6）→ 参考包自检（缺即停不写文件）→ 版本三分支（<34 更新/=34 询问/>34 停止）→ deploy.py 一键 → verify → sentinel+`.agents-pending-restart`。运行时门禁（deploy.py:118-136 与 SKILL.md 口径一致）T5 实测生效。
- **链 2 settings 合并**：闭合。find_python 探测 → merge-claude-settings.py 按 **command 身份**（`/.claude/hooks/<名>`）剥离受管注册再追加模板 → 用户 hook/顶层字段保留 → 原子写（mkstemp+fsync+os.replace）→ deploy.py 回读验 JSON。幂等（剥离+重加）T2 实测。
- **链 3 CLAUDE.md 三分支**：闭合。不存在→模板生成；有 `##`→section 合并（模板 5 标准节覆盖同名、用户独有保留，T3 验证）；无 `##`→CONFLICT 不动（T4 验证）。
- **链 4 agent-references 同路径检测**：闭合。realpath 判定符号链接安装（npx 项目级）自复制跳过，仅校验（deploy.py:170-183）。
- **链 5 版本权威**：UPGRADING.md 头部 ↔ deploy.py DEFAULT 常量 ↔ sentinel 模板 ↔ session-start 守卫（`-lt 34`/`-gt 34`/低于 v34/高于 v34 实测在位）——经 bump 脚本 dry-run 35 预览 41 处全列（含 deploy.py:12/:54、session-start.sh:71-75）✓；盲区见需修 1。

## 五、产消对账（Step 3b）

**产出侧**（逐项有消费方）：

| 产出 | 消费方 | 定级 |
|---|---|---|
| `.claude/hooks/`（8 .sh + core.js/cli.js + lib） | settings-hooks.json 注册 8 条（SessionStart×2/SessionEnd/PreToolUse×2/PostToolUse/PreCompact/PostCompact）→ Claude Code 运行时 | 显式消费 ✓ |
| `.claude/agents/`×8 | 各 skill spawn；moshu-review `Effective Mode: full/lean` 判定 | 显式消费 ✓ |
| `.claude/rules/`×4（paths frontmatter） | Claude Code path-scoped 规则 | 显式消费 ✓ |
| agent-references 34 项 | agents 的 canonical 路径 `.claude/skills/`（closure 114 绿） | 显式消费 ✓ |
| `.story-deployed` | session-start.sh（sentinel.sh 读取）+ 全 skill 入口门 | 显式消费 ✓ |
| `.agents-pending-restart` | session-start.sh 消费后自删（deploy-manual:70 文档化） | 显式消费 ✓ |
| CLAUDE.md 5 节 | 主会话路由/协作规则 | 显式消费 ✓ |

**输入侧**：`skills/moshu/VERSION`（SKILL.md:16 读）实测存在 ✓；merge helper 存在性由 Phase 1 自检覆盖 ✓。反向无断裂。

## 六、一致性（Step 4）

- `bump-agents-version.py 35`（dry-run，默认即预览）：41 处出现点全列且一致【事实】。
- **工具盲区（需修 1 证据）**：dry-run 41 处**不含** UPGRADING.md:8 与 deploy-manual.md:71/107/108 的 `` `33` `` 阈值字面——deploy-manual 处理器只匹配 `agents_version: N` 字面（bump-agents-version.py:103-107），UPGRADING 处理器只匹配版本头+升级步骤行且排除「变更」行（:110-113）。工具与守卫双盲区。
- README 计数口径：8 agents（含 moshu-evaluator 行）✓ / 8 hooks ✓，与模板目录实测一致。

## 七、历史回归（Step 5）

| 已修项 | 复验 | 结果 |
|---|---|---|
| deploy.py DEFAULT 常量（观察 007/008） | bump dry-run 覆盖 :12/:54 | ✅ 无回潮 |
| session-start 版本守卫 | :71-75 四字面全 34 | ✅ 无回潮 |
| deploy verify agents==8（B30） | :276 `== 8`，T1 PASS | ✅ 无回潮 |
| genre-prose-cards 主文件 setup 同步（B28） | 组 targets 含 setup 路径 | ✅ 无回潮 |
| plot-emotion-system setup 可达（B29） | 组 targets 含 setup 路径 | ✅ 无回潮 |
| 安装会话版本展示（test2-3 观察） | SKILL.md:16-18 在位 | ✅ 无回潮 |
| **B28 同类洞·文风卡半边** | 32 张卡 setup 副本**未登记**（§九 需修 2） | ⚠️ 残留半边 |

## 八、分级清单（Step 6）

### 阻断
**无**。

### 需修（3）

1. **版本阈值散射残留（bump 工具+守卫双盲区）**【事实】——UPGRADING.md:8（`小于 \`33\``、`大于 \`33\``、`不得用 v33` 共 3 字面）与 deploy-manual.md:71/107/108（`` `33` `` 共 4 字面）仍是 33 世代阈值；热路径 SKILL.md:23-25 已是 34。语义冲突实例：项目部署于 v33 时，SKILL.md:23 判「待更新」（正确，v34 新增 evaluator），deploy-manual:107/108 的 33 阈值双双落空（33 既不小于也不大于 33）→ 项目被当作「已最新」无需动作（错误）；项目部署于 v34 时，deploy-manual:108 判「大于 33 → skill 过旧停止」（错误，本地 skill 即当前版）。修法方向：bump 脚本补 `小于 \`{old}\`` / `大于 \`{old}\`` / 限定语境 `v{old}` 三模式（UPGRADING+deploy-manual 两文件），或改写这些行消除裸字面；属 v2.3.0 CI 红链同源问题。
2. **32 张题材文风卡 setup 副本未登记 shared-assets**【事实】——组 `genre-prose-card-{题材}` 的 targets 仅含 build 副本；setup 副本 `agent-references/genre-prose-cards/*.md` 不在任何组。当前三处字节一致（东方仙侠 b59493b9 实测，三处 md5 复验相同），但 `check-shared-files.sh` 只查已登记目标——卡片更新时 setup 副本静默漂移，用户部署拿到旧卡。B28 只修了主文件 genre-prose-cards.md，卡的半边漏了。修法方向：32 组 targets 补 setup 路径 → sync → check-shared-files 绿。
3. **Phase 3 计数口径过期（B30 迁移残留）**【事实】——SKILL.md:61「7 个 agents …五项」vs deploy.py verify 实测 **8 个 agents / 7 项检查**（T1b）；deploy-manual.md:12「7 agent files exist」同病（:77 已是 8，同文件自相矛盾）。修法方向：两处改 8；SKILL.md:61 清单补 settings 检查项。

### 候选（7）

4. **CLAUDE.md 合并首次重部署一次性规范化**【实测】——SKILL.md:57 声明「合并算法重复执行结果一致」，实测首次生成→首次合并字节变化（节间 1 空行→2 空行），第二次起收敛（第 3/4 次 md5 稳定 8ad4d76e）。非数据风险、非无限增长（初判被 T2b 推翻，见 §十.1），但严格幂等声明不成立。修法方向：`merge_claude_md` 各 block rstrip 后以 `\n\n` 统一 join。
5. **CONFLICT 路径 sentinel 照写 + verify 不查 CLAUDE.md**【实测】——T4：纯自定义 CLAUDE.md 时 deploy exit 0、sentinel 已写、verify 全绿，未部署 CLAUDE.md 的项目表面「完整部署」。SKILL.md:38 有「CONFLICT→人工处理」指令兜底，但状态无机械暴露。修法方向：verify 增加「CLAUDE.md 含模板标准节」检查（CONFLICT 未解决→FAIL），或 SKILL.md 明示 CONFLICT 时部署完整性语义。
6. **UPGRADING.md:12 格式坏**【事实】——v32→v33 / v31→v32 / v30→v31 三条目挤一行且含字面 `\n\n` 转义残留（生成痕迹）。
7. **deploy.py:13 docstring 用法形态错**【事实】——`deploy.py --verify {项目}` 应为 `deploy.py verify --project {项目}`（argparse 实体为子命令形态；SKILL.md:37 用的正确形态）。
8. **deploy-manual 清单与 deploy.py 常量漂移**【事实】——:98 合并策略列 4 个标准 section，deploy.py:50 `MANAGED_SECTIONS` 为 5 个（缺「作者控制点」，模板实测 5 节）；:16 sentinel 行列 5 字段，SENTINEL_FIELDS 为 6（缺 `deployed_at`）。文档-代码双份维护的典型漂移。
9. **setup 流程称谓 Phase 1-3 / Step 1-7 与全仓 Stage 制并存**【事实】——开发标准 §2.1b 若按通用性原则覆盖 setup，则 setup 属未迁移存量；建议作者裁决是否纳入后续称谓统一批。
10. **`.tmp/` 未进 .gitignore**【事实】——依赖「用完即删」纪律防误提交；加一行即可消险。

### 存疑（1）

11. **Windows 下 chmod/os.X_OK 语义**——本地 T1 verify「可执行」PASS，但 Windows 的 X_OK 近似恒真，本地结果不可证伪；跨平台真实性由 `cross-platform.yml` CI 承担。

## 九、性能与瘦身评估

setup 侧健康：SKILL.md 98 行远低于预算，deploy.py 370 行单文件清晰，无冷热分离或瘦身必要。**结构性建议（P1）**：本次需修 3 与候选 8 的共同根因是「deploy-manual Step 1 清单表与 deploy.py 检查逻辑双份维护」——建议后续批把 deploy-manual 表中数字类断言（agent 数、字段数）改为指向 `deploy.py verify` 为唯一权威（「见 verify 输出」），文档只述流程不复制数字。

## 十、自我推翻记录

1. **「CLAUDE.md 每轮部署增长」初判 → 推翻为一次性规范化**：T2 首轮 md5 变化曾疑不收敛；T2b 连续两次重部署 md5 稳定，实为首次合并的空白规范化，之后为不动点——降级候选 4。
2. **「check-current-skill-contracts.sh 红」初判疑真 → 推翻为平台假红**：.sh wrapper 在本机被 python 语义误跑；.py 直跑通过。
3. **「templates 26 文件未登记疑违 §5.1」初判 → 推翻为单源**：全仓查重无第二副本，登记前提不成立。
4. **「bump dry-run 0 命中疑工具失效」初判 → 推翻为参数误用**：`--dry-run` 非法旗标且 stderr 被吞；默认模式即预览，重跑 41 处正常——但顺带坐实阈值形态盲区（升级为需修 1）。

---

## 十一、复核勘误（2026-08-25）

复核人对本报告的载荷性论断做了独立抽验（转述必抽验纪律），两处修正、一处确认：

1. **文风卡数量勘误**：§八.2 与 §七 回归表的「30 张」应为 **32 张**——实测 write 源 / build 副本 / setup 副本三处均为 32 个文件（`ls *.md | wc -l`），shared-assets 卡组（不含主文件组）也恰为 32 个。需修 2 的实质（setup 副本未登记、守卫盲区）不受影响。
2. **需修 1 冲突实例改述**：原「项目部署于 33 时 deploy-manual:108 判停止」不成立（33 不大于 33，108 不触发）。已改为两个真实冲突形态：v33 项目被 107/108 双双落空误当「已最新」；v34 项目被 108 误判「skill 过旧停止」。
3. **字节一致性复验确认**：东方仙侠.md 三处 md5 均 `b59493b9103367f6d049415dfd97032b`（复现命令：`md5sum` 三路径），§八.2 的「当前字节一致」论断成立。

*报告完。本审计只查不改；修复建议见 §八，走作者发起的新规格批次。实测临时目录已清理。*
