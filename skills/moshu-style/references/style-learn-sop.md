# 文风学习 SOP（style-learn-sop.md）

> **何时加载**：moshu-style Step 4 执行时。本文件是从任意量原文提取写作风格（表达层）的详细操作步骤——**不依赖拆书任何产物**（黄金三章深度拆解/章节摘要/拆文报告均不需要），对话技法从样本原文直接归纳。
>
> **输出**：`文风库/文风.md`（模板见 SKILL.md「产出规范」）。

## 前置

- 样本已准备（Step 3）：`文风库/_source.md` 或内存中的 2-3 段样本（各约 1000 字）
- 样本 <800 字（粘贴片段）→ 全程 confidence: low，并提示用户补充

## Step A: 句长/标点/段落节奏（确定性统计）

由**主线程**执行。把样本拼成单文件喂给下面的脚本（heredoc 作 Python 源，样本路径按 argv 传入）。先探测可用解释器再跑——**勿直接用 `python3`**，Windows 上它会触发 Microsoft Store 占位程序、exit 49 失败。样本路径**必须用项目内相对路径**（Windows 原生 python 会把 `/tmp/x.txt` 解析成 `C:\tmp\x.txt`，与 Git Bash 写入位置不一致）：

```bash
SAMPLE="文风库/_source.md"   # 或实际样本路径
for PYBIN in python3 python py; do "$PYBIN" -c "" 2>/dev/null && break; done
"$PYBIN" - "$SAMPLE" <<'PYEOF'
import re
import sys
with open(sys.argv[1], 'r', encoding='utf-8') as f:
    text = f.read()
sents = [s for s in re.split(r'[。！？]+', text) if s.strip()]
total = max(len(sents), 1)
short = sum(1 for s in sents if len(s) < 15)
mid   = sum(1 for s in sents if 15 <= len(s) <= 30)
lng   = sum(1 for s in sents if len(s) > 30)
chars = max(sum(1 for c in text if not c.isspace()), 1)
puncts = sum(1 for c in text if c in '，。！？；：、…—""\'\'')
avg = sum(len(s) for s in sents) // total
print(f'sentences={total}; short_lt15={100*short//total}%; mid_15to30={100*mid//total}%; long_gt30={100*lng//total}%; avg_len={avg}; punct_density={100*puncts//chars}%')
PYEOF
```

实测输出形如 `sentences=6; short_lt15=66%; mid_15to30=33%; long_gt30=0%; avg_len=12; punct_density=15%`。把数值直接填进模板「整体语感」——`confidence: high`（确定性测量，不是抽样估计）。

**段落节奏**：从样本人工归纳——平均段长（每段行数/字数估算）、单段单动作 vs 多动作堆叠、断行习惯。

**Bash/Python 不可用时的降级**：跳过确定性统计；句长段写「解释器不可用，跳过确定性统计」；`confidence: low`。

## Step B: 对话技法（从样本直接归纳）

- **潜台词模式**：扫描样本中的对话段落，识别 2-3 种典型手法——问非所答、语气反差、信息隐瞒、话里有话等；每种附 1 段原文示例（300 字内）
- **对话标签习惯**：样本中说话动词的多样性（说/道/问/喊 vs 重复单一）、动作替代说话标签的频率、对话与动作的穿插比例
- **角色语气区分**：样本含多个说话者时，归纳主角和 1-2 个核心配角的句式差异（口头禅/句长/用词），引用原文样本句
- 样本无对话（纯独白/纯设定）→ 对话技法段写「样本无对话，跳过」或省略，不编造

## Step C: 原文锚点片段（2-4 段）

- 从样本中选 2-4 段，**优先对话+动作交织的段落**（纯独白/纯设定段不选）
- 每段 300-500 字；基调按样本内容判断标注（紧张/悲伤/轻松/热血等；样本不足的基调写明跳过，不编造）
- **锚点必须逐字连续切片，禁止改写/缩写/跳段/拼接**：moshu-narrative-writer 拿锚点当 few-shot 直接学，标注的行号要能回查来源。落盘前逐段抽 1-2 句 `grep -F` 回 `文风库/_source.md`（粘贴来源）或原文文件，grep 不到即说明被改写或拼接——重切为忠实连续片段。确需跳过中间过渡段时，分别标各自真实行号（如「行264-267 + 行269-270」）并在引用块内用「（……中略……）」显式断开
- 少于 1 段 → `文风可用：否：锚点不足`（few-shot 核心缺失）

## Step D: 落盘

按 SKILL.md「产出规范」模板填写 `文风库/文风.md`：

- **生成记录**：来源（本地文件路径/粘贴）、抽样位置、生成时间、`文风可用：是/否`
- **覆盖前确认**：`文风库/文风.md` 已存在 → AskUserQuestion「替换现有文风？」
- 每段标 confidence（high=确定性统计 / med=样本归纳充足 / low=样本不足或降级）

## 失败模式与降级

| 场景 | 降级策略 |
|---|---|
| 源文件不存在/不可读 | 提示重新提供路径；粘贴场景不存在此问题 |
| 非 UTF-8 且转码失败 | 报错说明编码，提示转码后重试 |
| 样本 <800 字 | 全程 confidence: low；提示用户补充 |
| Python 解释器不可用 | 跳过句长统计，confidence: low |
| 样本无对话 | 对话技法段省略，不编造 |
| 锚点不足 1 段 | `文风可用：否：锚点不足` |

## 与拆书的关系

- 本 SOP 是**纯表达层**方法论——不依赖拆书任何 Stage 产物
- 拆书 Stage 6「技法总结」产拆解结论（情绪交替/可借鉴技巧/分层建议/不可模仿）——与本文件互补不重叠
- 需要完整对标时：`/moshu-analyze` 全量拆解（情绪模块/节奏/技法总结）

## 与写书的关系

- `文风库/文风.md` = moshu-write 写前准备 (d) 文风召回唯一来源（每章必做）
- 缺失/不合规时写书侧交互提醒（「用 /moshu-style 生成 / 跳过用默认 Gate / 自写约束引导」）
- 写作时 narrative-writer 消费：句长带（自检）/ 锚点（few-shot）/ 对话技法（潜台词优先）
