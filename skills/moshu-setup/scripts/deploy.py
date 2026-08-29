#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""moshu-setup 一键部署器（Stage 2-3 的确定性部分）

把 hooks/rules/agents/agent-references/settings/sentinel/CLAUDE.md 的
复制、chmod、同路径检测、合并、校验一次跑完——AI 只保留探测判断、
AskUserQuestion 与结果报告，不再逐条手写 cp/chmod（三层分工：脚本做确定性的）。

用法（按仓库解释器探测形态调用，Windows 禁止裸 python3）:
  for PYBIN in python3 python py; do "$PYBIN" -c "" 2>/dev/null && break; done
  "$PYBIN" deploy.py --project {项目目录} --name {项目名} [--book {书名}]
                     [--agents-version 44] [--setup-version 1.5.1] [--dry-run]
  "$PYBIN" deploy.py verify --project {项目目录}

行为:
  - 幂等: managed 文件 replace；用户状态文件 create-only-if-absent
  - CLAUDE.md: 不存在→模板占位符替换生成；存在→按 `##` section 合并
    （模板标准 section 覆盖同名、用户独有 section 保留）；纯自定义无 section
    文件→报 CONFLICT 不覆盖（留给 AI 按合并策略处理）
  - agent-references: 符号链接安装同路径检测，相同则跳过复制仅校验
  - settings.local.json: 复用 merge-claude-settings.py（subprocess 调用）
  - sentinel/restart 标记: 按 .story-deployed 模板写入
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATES = SKILL_DIR / 'references' / 'templates'
AGENT_REFS = SKILL_DIR / 'references' / 'agent-references'
MERGE_HELPER = SKILL_DIR / 'scripts' / 'merge-claude-settings.py'

# CLAUDE.md 模板标准 section 列表（合并时这些标题由模板权威覆盖）
MANAGED_SECTIONS = ('Skill 路由表', '文件结构', '协作规则', '作者控制点',
                    'Compact 后恢复上下文')
# 标题匹配不跨行（[ \t] 而非 \s）：re.M 下 \s*$ 会贪婪吃掉标题行尾换行，导致 split_sections
# 的 body 丢失一个 \n、合并输出与模板渲染不一致（幂等破坏，候选 4）
SECTION_RE = re.compile(r'^##[ \t]+(.+?)[ \t]*$', re.M)

DEFAULT_AGENTS_VERSION = '44'
DEFAULT_SETUP_VERSION = '1.5.1'
SENTINEL_FIELDS = ('deployed_at', 'agents_version', 'setup_skill_version', 'target_cli',
                   'resolver_strategy', 'references_dir')


class DeployFatal(Exception):
    """部署过程中不可继续的致命错误。"""


def find_python():
    for cand in ('python3', 'python', 'py'):
        try:
            r = subprocess.run([cand, '-c', ''], capture_output=True)
            if r.returncode == 0:
                return cand
        except FileNotFoundError:
            continue
    return None


def render_claude_md(name: str, book: str) -> str:
    tmpl = (TEMPLATES / 'CLAUDE.md.tmpl').read_text(encoding='utf-8')
    # 统一 LF 行尾：模板文件可能 CRLF（Windows 工作区），生成/合并两路径必须字节一致才幂等（候选 4）
    rendered = tmpl.replace('{项目名}', name).replace('{书名}', book).replace('\r\n', '\n')
    # 残留校验：模板若出现未替换的 {占位符}（模板新增字段而 render 未跟进），生成的 CLAUDE.md
    # 会把字面占位符带进用户项目——fatal 拦截而不是静默产出坏文件
    leftover = re.search(r'\{[^}]*\}', rendered)
    if leftover:
        raise DeployFatal(
            f'CLAUDE.md 模板存在未替换占位符：{leftover.group(0)}——'
            '检查 templates/CLAUDE.md.tmpl 与 render_claude_md 的占位符集合'
        )
    return rendered


def split_sections(text: str):
    """按 `## ` 标题切分 section，返回 [(title, body), ...]"""
    matches = list(SECTION_RE.finditer(text))
    if not matches:
        return []
    out = []
    for i, m in enumerate(matches):
        title = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        out.append((title, text[start:end]))
    return out


def merge_claude_md(existing: str, template_rendered: str) -> str:
    """模板 section 覆盖同名，用户独有 section 保留（无 marker 时的 section 合并）"""
    # 统一 LF 行尾后再合并：老项目 CLAUDE.md 可能 CRLF，规范化保证输出与生成路径一致（幂等，候选 4）
    existing = existing.replace('\r\n', '\n')
    template_rendered = template_rendered.replace('\r\n', '\n')
    tpl_sections = split_sections(template_rendered)
    if not tpl_sections:
        return template_rendered
    usr_sections = split_sections(existing)
    tpl_titles = {t for t, _ in tpl_sections}
    # 头部（模板 `# 标题` 到第一个 `##` 之前）——用 search 定位，避免 re.M 缺失
    first = SECTION_RE.search(template_rendered)
    head = template_rendered[:first.start()] if first else template_rendered
    kept_usr = [(t, b) for t, b in usr_sections if t not in tpl_titles]
    # 各 block rstrip 后以 \n\n 统一 join：与模板渲染输出字节一致 → 合并是幂等不动点
    # （审计-setup-v1 候选 4：旧实现 body 原样拼接导致首次合并多出空行、SKILL.md「重复执行结果一致」声明不成立）
    blocks = [head.rstrip()]
    for t, b in tpl_sections:
        blocks.append(f'## {t}{b.rstrip()}')
    for t, b in kept_usr:
        blocks.append(f'## {t}{b.rstrip()}')
    return '\n\n'.join(blocks) + '\n'


def deploy(project: Path, name: str, book: str, agents_ver: str, setup_ver: str,
           dry_run: bool) -> tuple[list[str], list[str]]:
    logs: list[str] = []
    fatal: list[str] = []

    # 版本门禁：禁止降级覆盖（与 moshu-setup SKILL.md Stage 1 口径一致）
    sentinel = project / '.story-deployed'
    if sentinel.exists():
        try:
            sentinel_text = sentinel.read_text(encoding='utf-8')
        except OSError as e:
            raise DeployFatal(f'无法读取已有 .story-deployed：{e}')
        m = re.search(r'^agents_version:\s*(\d+)', sentinel_text, re.M)
        if m:
            existing_agents = int(m.group(1))
            try:
                current_agents = int(agents_ver)
            except ValueError:
                current_agents = -1
            if existing_agents > current_agents:
                raise DeployFatal(
                    f'项目已部署 agents_version={existing_agents}，大于当前 {agents_ver}；'
                    '请先更新 mo-shu，禁止降级覆盖。'
                )

    hooks_src = TEMPLATES / 'hooks'
    hooks_dst = project / '.claude' / 'hooks'
    rules_src = TEMPLATES / 'rules'
    rules_dst = project / '.claude' / 'rules'
    agents_src = TEMPLATES / 'agents'
    agents_dst = project / '.claude' / 'agents'

    # --- hooks（递归复制 + 顶层 *.sh chmod；lib 不要求执行位） ---
    # managed 目录清空重建（replace 语义）：rmtree 防旧版本残留文件留在用户项目被误执行
    if not dry_run:
        try:
            if hooks_dst.exists():
                shutil.rmtree(hooks_dst)
            shutil.copytree(hooks_src, hooks_dst)
            for sh in hooks_dst.glob('*.sh'):
                sh.chmod(sh.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        except OSError as e:
            fatal.append(f'hooks 复制失败: {e}')
    logs.append(f'hooks: {len(list(hooks_dst.glob("*.sh")))} 脚本 + lib/ (chmod 顶层 *.sh)')

    # --- rules / agents（replace：清空重建） ---
    if not dry_run:
        try:
            if rules_dst.exists():
                shutil.rmtree(rules_dst)
            if agents_dst.exists():
                shutil.rmtree(agents_dst)
            rules_dst.mkdir(parents=True, exist_ok=True)
            agents_dst.mkdir(parents=True, exist_ok=True)
            for f in rules_src.glob('*.md'):
                shutil.copy2(f, rules_dst / f.name)
            for f in agents_src.glob('*.md'):
                shutil.copy2(f, agents_dst / f.name)
        except OSError as e:
            fatal.append(f'rules/agents 复制失败: {e}')
    logs.append(f'rules: {len(list(rules_src.glob("*.md")))} | agents: {len(list(agents_src.glob("*.md")))}')

    # --- agent-references（同路径检测；相同跳过复制仅校验） ---
    ref_dst = project / '.claude' / 'skills' / 'moshu-setup' / 'references' / 'agent-references'
    same_path = os.path.realpath(AGENT_REFS) == os.path.realpath(ref_dst)
    if not dry_run and not same_path:
        try:
            if ref_dst.exists():
                shutil.rmtree(ref_dst)
            ref_dst.mkdir(parents=True, exist_ok=True)
            for f in AGENT_REFS.glob('*'):
                if f.is_dir():
                    shutil.copytree(f, ref_dst / f.name)
                else:
                    shutil.copy2(f, ref_dst / f.name)
        except OSError as e:
            fatal.append(f'agent-references 复制失败: {e}')
    missing = [str(f.relative_to(AGENT_REFS)) for f in AGENT_REFS.rglob('*') if f.is_file() and not (ref_dst / f.relative_to(AGENT_REFS)).exists()]
    logs.append(f'agent-references: {"同路径跳过复制" if same_path else "已复制"} {len(list(AGENT_REFS.iterdir()))} 项' +
                (f' | 缺失: {missing}' if missing else ' | 全部在位'))

    # --- CLAUDE.md（不存在生成 / 存在 section 合并 / 纯自定义报 CONFLICT） ---
    md_path = project / 'CLAUDE.md'
    rendered = render_claude_md(name, book)
    if not md_path.exists():
        if not dry_run:
            try:
                md_path.write_text(rendered, encoding='utf-8')
            except OSError as e:
                fatal.append(f'CLAUDE.md 写入失败: {e}')
        logs.append('CLAUDE.md: 已生成（占位符替换）')
    else:
        try:
            existing = md_path.read_text(encoding='utf-8')
        except OSError as e:
            fatal.append(f'CLAUDE.md 读取失败: {e}')
            existing = ''
        if existing.strip() and SECTION_RE.search(existing):
            if not dry_run:
                try:
                    md_path.write_text(merge_claude_md(existing, rendered), encoding='utf-8')
                except OSError as e:
                    fatal.append(f'CLAUDE.md 写入失败: {e}')
            logs.append('CLAUDE.md: 已按 section 合并（模板覆盖同名，用户独有保留）')
        elif existing.strip():
            logs.append('CLAUDE.md: CONFLICT 无 ## section，未覆盖（交由 AI 按合并策略处理）')
        else:
            # 空文件（无用户数据）→ 生成覆盖安全（此前误判 CONFLICT 逼 AI 人工处理）
            if not dry_run:
                try:
                    md_path.write_text(rendered, encoding='utf-8')
                except OSError as e:
                    fatal.append(f'CLAUDE.md 写入失败: {e}')
            logs.append('CLAUDE.md: 已生成（空文件覆盖）')

    # --- settings.local.json（复用 merge helper） ---
    settings_path = project / '.claude' / 'settings.local.json'
    if not dry_run:
        pybin = find_python()
        if pybin is None:
            fatal.append('settings: FAIL 未找到 python 解释器，无法合并 hooks 配置')
        else:
            cmd = [pybin, str(MERGE_HELPER), '--existing', str(settings_path),
                   '--template', str(TEMPLATES / 'settings-hooks.json'),
                   '--output', str(settings_path)]
            r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
            if r.returncode != 0:
                fatal.append(f'settings: FAIL merge helper exit={r.returncode} {r.stderr[-200:]}')
            else:
                try:
                    json.loads(settings_path.read_text(encoding='utf-8'))
                    logs.append('settings: 已合并（merge-claude-settings.py），JSON 有效')
                except json.JSONDecodeError as e:
                    fatal.append(f'settings: FAIL JSON 无效 {e}')
    else:
        logs.append('settings: (dry-run 不执行 merge)')

    # --- sentinel + restart 标记（仅全部必需步骤 PASS 后写入） ---
    if fatal:
        logs.append('部署未完成：存在 fatal 错误，未写入 sentinel/restart 标记')
        return logs, fatal

    if not dry_run:
        now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        sentinel.write_text(
            f'deployed_at: {now}\n'
            f'agents_version: {agents_ver}\n'
            f'setup_skill_version: {setup_ver}\n'
            'target_cli: claude-code\n'
            'resolver_strategy: project-local-skill-reference\n'
            'references_dir: .claude/skills/moshu-setup/references/agent-references\n',
            encoding='utf-8')
        (project / '.claude' / '.agents-pending-restart').touch()
    logs.append('sentinel + .agents-pending-restart: 已写入')
    return logs, fatal


def verify(project: Path) -> list[str]:
    checks: list[str] = []
    ok = True

    def check(name: str, cond: bool, detail: str = ''):
        nonlocal ok
        checks.append(f'{"PASS" if cond else "FAIL"}  {name}  {detail}')
        if not cond:
            ok = False

    hooks = project / '.claude' / 'hooks'
    # 动态枚举模板 .sh（与 F 的 agents 动态化同模式）：新增/删除 hook 自动跟随，
    # 不再维护写死 8 文件名第三份名单（P2 成对一致性修复的漏网——模板增 hook 会漏检、删 hook 会误报）；
    # bool(tpl_sh) 防空模板假绿（审核 F4：空 glob 时 all() 对空迭代为 True）
    tpl_sh = list((TEMPLATES / 'hooks').glob('*.sh'))
    check('hooks 顶层脚本可执行', bool(tpl_sh) and all(
        (hooks / f.name).is_file() and os.access(hooks / f.name, os.X_OK)
        for f in tpl_sh))
    check('hooks lib 在位', (hooks / 'lib' / 'common.sh').is_file() and (hooks / 'lib' / 'sentinel.sh').is_file())
    rules = project / '.claude' / 'rules'
    rules_ok = rules.is_dir() and all(
        f.is_file() and 'paths:' in f.read_text(encoding='utf-8', errors='ignore')
        for f in rules.glob('*.md'))
    check('rules 含 paths frontmatter', rules_ok)
    agents = project / '.claude' / 'agents'
    check('agents 模板齐全（源目标一致）', len(list(agents.glob('*.md'))) == len(list((TEMPLATES / 'agents').glob('*.md'))))
    ref_dst = project / '.claude' / 'skills' / 'moshu-setup' / 'references' / 'agent-references'
    same_path = os.path.realpath(AGENT_REFS) == os.path.realpath(ref_dst)
    ref_ok = same_path or all((ref_dst / f.relative_to(AGENT_REFS)).exists() for f in AGENT_REFS.rglob('*') if f.is_file())
    check('agent-references 在位（含 genre-prose-cards 子卡）', ref_ok)

    # settings：JSON 有效 + 模板命令必须各一份
    try:
        tpl = json.loads((TEMPLATES / 'settings-hooks.json').read_text(encoding='utf-8'))
        tpl_cmds = [hook.get('command', '') for blocks in tpl.get('hooks', {}).values()
                    for b in blocks if isinstance(b, dict)
                    for hook in b.get('hooks', []) if isinstance(hook, dict)]
    except Exception as e:
        tpl_cmds = []
        check('settings 模板可读', False, str(e))
    settings = project / '.claude' / 'settings.local.json'
    try:
        d = json.loads(settings.read_text(encoding='utf-8'))
        cmds = [h.get('command', '') for evt, blocks in d.get('hooks', {}).items()
                for b in blocks for h in b.get('hooks', [])]
        dup = {c for c in cmds if cmds.count(c) > 1}
        missing = [c for c in tpl_cmds if c not in cmds]
        check('settings JSON 有效且模板命令齐全、无重复', bool(d) and not dup and not missing,
              f'缺失模板命令: {missing}' if missing else '')
    except Exception as e:
        check('settings JSON 有效且模板命令齐全、无重复', False, str(e))

    # sentinel：6 字段 + 版本值必须等于当前部署版本
    sentinel = project / '.story-deployed'
    if sentinel.is_file():
        sentinel_text = sentinel.read_text(encoding='utf-8')
        fields_ok = all(re.search(rf'^{k}:', sentinel_text, re.M) for k in SENTINEL_FIELDS)
        agents_m = re.search(r'^agents_version:\s*(\S+)', sentinel_text, re.M)
        setup_m = re.search(r'^setup_skill_version:\s*(\S+)', sentinel_text, re.M)
        values_ok = bool(
            agents_m and agents_m.group(1).strip() == DEFAULT_AGENTS_VERSION
            and setup_m and setup_m.group(1).strip() == DEFAULT_SETUP_VERSION
        )
        check('sentinel 6 字段且版本值正确', fields_ok and values_ok)
    else:
        check('sentinel 6 字段且版本值正确', False)

    # CLAUDE.md 标准节检查（审计-setup-v1 候选 5：CONFLICT 未解决时机械暴露——纯自定义 CLAUDE.md 走 CONFLICT 后 verify 必须能看出「未部署完整」）
    md_path = project / 'CLAUDE.md'
    if md_path.is_file():
        md_lines = md_path.read_text(encoding='utf-8', errors='ignore').splitlines()
        # 前缀匹配：模板节标题可带后缀（如「作者控制点（你只负责这几件事）」），等值匹配会误报缺失
        missing_sections = [s for s in MANAGED_SECTIONS if not any(l.strip().startswith(f'## {s}') for l in md_lines)]
        check('CLAUDE.md 含全部模板标准节', not missing_sections,
              f'缺失标准节: {missing_sections}' if missing_sections else '')
    else:
        check('CLAUDE.md 含全部模板标准节', False, 'CLAUDE.md 不存在')
    checks.append('RESULT: ' + ('ALL PASS' if ok else 'HAS FAILURE'))
    return checks


def main():
    ap = argparse.ArgumentParser(description='moshu-setup 一键部署器')
    sub = ap.add_subparsers(dest='cmd', required=True)
    d = sub.add_parser('deploy', help='执行完整部署')
    d.add_argument('--project', required=True)
    d.add_argument('--name', required=True, help='项目名（CLAUDE.md 占位符）')
    d.add_argument('--book', default=None, help='书名（缺省=项目名）')
    d.add_argument('--agents-version', default=DEFAULT_AGENTS_VERSION)
    d.add_argument('--setup-version', default=DEFAULT_SETUP_VERSION)
    d.add_argument('--dry-run', action='store_true')
    v = sub.add_parser('verify', help='Stage 3 验证')
    v.add_argument('--project', required=True)
    args = ap.parse_args()

    project = Path(args.project).resolve()
    if not project.is_dir():
        print(f'[错误] 项目目录不存在: {project}', file=sys.stderr)
        sys.exit(2)

    if args.cmd == 'deploy':
        try:
            logs, fatal = deploy(project, args.name, args.book or args.name,
                                 args.agents_version, args.setup_version, args.dry_run)
        except DeployFatal as e:
            print(f'[错误] {e}', file=sys.stderr)
            sys.exit(1)
        for line in logs:
            print(' -', line)
        if fatal:
            print('[错误] 部署未完成，存在以下 fatal 问题：', file=sys.stderr)
            for line in fatal:
                print(f'  - {line}', file=sys.stderr)
            print('手动修复步骤：', file=sys.stderr)
            print('  1. 按上方 fatal 信息修复对应文件/环境问题；', file=sys.stderr)
            print('  2. settings 合并失败时，先检查 .claude/settings.local.json 是否为合法 JSON；', file=sys.stderr)
            print('  3. 确认 Python 解释器可用（python3/python/py 任一）；', file=sys.stderr)
            print('  4. 修复后重新运行 deploy.py deploy，成功前不会写入 .story-deployed。', file=sys.stderr)
            sys.exit(1)
    else:
        lines = verify(project)
        failed = any('HAS FAILURE' in line for line in lines)
        for line in lines:
            print(line)
        if failed:
            # 审计-V3 PM1：验证失败必须以非零退出码暴露（此前恒 0，脚本/CI 包装会把失败当通过）
            sys.exit(1)


if __name__ == '__main__':
    main()
