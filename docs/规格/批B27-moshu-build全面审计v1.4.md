# 规格 · 批 B27：moshu-build 全面审计（审计法 v1.4）+ 性能优化与瘦身评估

- 版本：v1.0（2026-08-24）
- 前置依赖：审计法 v1.4 已入库（`0c9850e`）；B14-B26 已全部合入。
- 依据：作者指示"按审计法 SOP 重做一轮完整的 moshu-build 审计，审计完之后看看能否进行性能优化，代码瘦身"。

---

## 一、任务定义

**按 `docs/审计法.md` v1.4 的六步流程**，对 `skills/moshu-build/` 做完整审计，产出审计报告。审计完成后基于发现做性能优化与代码瘦身的评估提案（只提案不施工——优化走后续批次）。

**关键约束**：审计只查不改——发现问题的唯一写入是审计报告文件；修复须另行走规格。性能优化/瘦身建议以候选清单形式附在报告尾部。

---

## 二、六步审计执行指引

### Step 1: 基线

```bash
export PYTHONIOENCODING=utf-8
# 全量守卫
for s in scripts/*.sh; do echo "=== $(basename $s) ==="; bash "$s" 2>&1 | tail -3; echo "exit=$?"; done
# 回归测试
for t in scripts/test-*.py; do echo "=== $(basename $t) ==="; python "$t" 2>&1 | tail -2; echo "exit=$?"; done
for t in scripts/test-*.js; do echo "=== $(basename $t) ==="; node "$t" 2>&1 | tail -2; echo "exit=$?"; done
```

记录全绿基线。任何红先判因（排三类假红：GBK/chmod/symlink），排除后才算真红——真红记录但不修。

### Step 2: 结构与引用审计

**2a 结构盘点**：
```bash
# 文件清单+体量
find skills/moshu-build -type f | sort
# 每文件行数
wc -l skills/moshu-build/references/*.md skills/moshu-build/scripts/*
# doc-budget 登记
python scripts/check-doc-budget.sh
```
安全面轻扫：check_outline.py / impact_scan.py 的 --project 参数是否限制在预期根内（防穿越）；输入文件解析失败是否明示三分类（缺/空/坏）。
冷热分离检查：workflow-build.md（热路径）内容是否全部高频消费——逐节统计在主流程中被引用次数，<2 次的为冷路径下沉候选。

**2b 引用内容抽检**：
- 热消费深读 2-3 个：选 workflow-build.md 高频指示加载的 outline-methods.md / character-design-methods.md / plot-emotion-system.md 深读——与当前 Stage 1-6 流程是否矛盾、苏格拉底问句是否完整、内部引用是否可达
- 过时信号全扫：`grep -rn "workflow-setup\|Phase [123]\|旧版\|已废弃" skills/moshu-build/references/`
- 体量异常：>700 行的标记为候选瘦身、<50 行的标记为候选充实
- **通用性四问**：对三节逆向萃取（势力场设计/升级绑弧光/舞台与规则设计）逐条过四问
- **苏格拉底问句有效性**：抽 2 个问句模拟回答——能否用 ≤5 字标签回答

**2c 填充测试**：
拿大奉打更人弧 1（税银案，第 1-40 章）的已知结构（章节标题实证），反填 moshu-build 的核心模板：
- 八列骨架表（用大奉弧 1 的实际内容填）
- 势力场总览（大奉弧 1 的势力关系）
- 中点假胜败（大奉弧 1 的中点是什么）
- 常驻压力（大奉弧 1 的贯穿压力是什么）
- 暗线层次（大奉弧 1 的暗线属于哪层）
填不顺处记录——区分库存缺/接线缺/深度缺。

### Step 3: 机制链与产消审计

**3a 机制链**（枚举 moshu-build 的端到端链）：
- 链 1：开书构建 Stage 1→6（正常路径走查 + 异常降级：缺理想书评/缺台账/中途关窗）
- 链 2：采风触发→researcher agent→产物回来→融合四步→喂 Stage 2
- 链 3：修订请求→impact_scan→裁决→落盘→stale 标记→消化→构建态翻回
- 链 4：开新卷（cold-path）→Stage 4 起增量→定稿→构建态翻回
- 链 5：Stage 6 定稿→tracking init→context JSON→write 侧消费
- 链 6：check_outline.py 机检→blocking 修→candidate 附屏
- 每链走查正常+异常+人机分工点+交互模态一致性

**3b 产消对账**：
- 正向：列出 moshu-build 的每个产出物（理想书评/题材定位/关系/题材正文提示卡/构建台账/大纲/角色弧线/世界观×2/单元卡/整合记录/卷纲/变更日志），逐个 grep 全仓找消费方，四级定级（显式消费/定位声明/**标签消费**/悬空）
- 反向：列出 moshu-build 的每个必需输入（.story-deployed/采风产物/卷复盘/审查工单），逐个找产出方，字段级吻合
- capability-wiring 对账
- 向后兼容核对

### Step 4: 一致性轻扫

```bash
# 版本散射专项（工具化）
python scripts/bump-agents-version.py 34 2>&1 | head -20  # dry-run 列全部出现点
# 术语表违例
grep -rn "上下文.md 检查点\|状态卡文件\|tracking 提交\|拆解库\|机器审查" skills/moshu-build/
# 悬空引用
python scripts/check-reference-closure.py
# 数字口径
bash scripts/check-story-numbers.sh
```

### Step 5: 历史回归

从 test2-1 和 test2-4 的使用观察文件中抽取已修项（观察 001-011 已处置的），逐个复验当前代码确认没有回潮。重点：
- deploy.py DEFAULT 常量是否仍是 33/1.5.1
- session-start.sh 是否仍正确（-lt 33 / -gt 33）
- check_outline.py 版本兼容降级是否仍工作
- 苏格拉底问句是否仍在方法论文件中
- Stage 命名是否有回潮为"步 N"

### Step 6: 分级汇总

按 v1.4 四档分级（阻断/需修/候选/存疑），每条带证据（路径:行号）+ 分档（事实/推断/存疑）。

---

## 三、性能优化与瘦身评估（审计完成后做）

基于审计发现，评估以下优化方向（只提案不施工）：

1. **workflow-build.md 瘦身**：当前 27K+ 字符——冷热分离检查发现的低频节是否可下沉
2. **方法论文件瘦身**：>700 行的大文件（plot-frameworks 711 行/plot-special-topics 637 行/character-design-methods 573 行）是否有重复/过时内容
3. **tracking_commit.py 瘦身**：1799 行是否可拆子命令
4. **按节精读的实际执行率**：指引是否真的让 AI 做了节级加载而非整文件读入（从 test2-4 的 Read 日志评估）
5. **共享面的瘦身**：90% references 共享——是否有 build 侧不需要的 write 侧文件被 sync 过来

---

## 四、产出

写入 `docs/审计-moshu-build-v1.4.md`，结构固定：
```
基线 / 结构盘点 / 机制链表 / 产消对账表 / 填充测试结果 / 一致性 / 历史回归 / 分级清单 / 性能优化与瘦身提案 / 自我推翻记录
```

---

## 五、禁止事项

1. **只查不改**——审计的唯一写入是审计报告文件
2. 发现的问题只呈报不修复——修复走后续规格批次
3. 候选永不拦截
4. 版本一致性验证必须用 bump 脚本 dry-run，禁止以手工 grep 作为唯一验证
5. 填充测试的残差必须区分库存缺/接线缺/深度缺

---

## 六、提交规范

`docs(审计): moshu-build 全面审计（审计法 v1.4 首次应用）——六步全流程含填充测试/标签消费检出/版本散射工具化；附性能优化与瘦身提案（B27）`
