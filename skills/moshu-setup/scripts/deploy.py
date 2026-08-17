#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""moshu-setup 一键部署器（Phase 2+3 的确定性部分）

把 hooks/rules/agents/agent-references/settings/sentinel/CLAUDE.md 的
复制、chmod、同路径检测、合并、校验一次跑完——AI 只保留探测判断、
AskUserQuestion 与结果报告，不再逐条手写 cp/chmod（三层分工：脚本做确定性的）。

用法（按仓库解释器探测形态调用，Windows 禁止裸 python3）:
  for PYBIN in python3 python py; do "$PYBIN" -c "" 2>/dev/null && break; done
  "$PYBIN" deploy.py --project {项目目录} --name {项目名} [--book {书名}]
                     [--agents-version 26] [--setup-version 1.2.9] [--dry-run]
  "$PYBIN" deploy.py --verify {项目目录}

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
SECTION_RE = re.compile(r'^##\s+(.+?)\s*$', re.M)


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
    return tmpl.replace('{项目名}', name).replace('{书名}', book)


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
    tpl_sections = split_sections(template_rendered)
    if not tpl_sections:
        return template_rendered
    usr_sections = split_sections(existing)
    tpl_titles = {t for t, _ in tpl_sections}
    # 头部（模板 `# 标题` 到第一个 `##` 之前）——用 search 定位，避免 re.M 缺失
    first = SECTION_RE.search(template_rendered)
    head = template_rendered[:first.start()] if first else template_rendered
    kept_usr = [(t, b) for t, b in usr_sections if t not in tpl_titles]
    blocks = [head]
    for t, b in tpl_sections:
        blocks.append(f'## {t}{b}')
    for t, b in kept_usr:
        blocks.append(f'## {t}{b}')
    return '\n'.join(blocks).rstrip('\n') + '\n'


def deploy(project: Path, name: str, book: str, agents_ver: str, setup_ver: str,
           dry_run: bool) -> list[str]:
    logs: list[str] = []
    hooks_src = TEMPLATES / 'hooks'
    hooks_dst = project / '.claude' / 'hooks'
    rules_src = TEMPLATES / 'rules'
    rules_dst = project / '.claude' / 'rules'
    agents_src = TEMPLATES / 'agents'
    agents_dst = project / '.claude' / 'agents'

    # --- hooks（递归复制 + 顶层 *.sh chmod；lib 不要求执行位） ---
    if not dry_run:
        shutil.copytree(hooks_src, hooks_dst, dirs_exist_ok=True)
        for sh in hooks_dst.glob('*.sh'):
            sh.chmod(sh.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    logs.append(f'hooks: {len(list(hooks_dst.glob("*.sh")))} 脚本 + lib/ (chmod 顶层 *.sh)')

    # --- rules / agents（replace） ---
    if not dry_run:
        rules_dst.mkdir(parents=True, exist_ok=True)
        agents_dst.mkdir(parents=True, exist_ok=True)
        for f in rules_src.glob('*.md'):
            shutil.copy2(f, rules_dst / f.name)
        for f in agents_src.glob('*.md'):
            shutil.copy2(f, agents_dst / f.name)
    logs.append(f'rules: {len(list(rules_src.glob("*.md")))} | agents: {len(list(agents_src.glob("*.md")))}')

    # --- agent-references（同路径检测；相同跳过复制仅校验） ---
    ref_dst = project / '.claude' / 'skills' / 'moshu-setup' / 'references' / 'agent-references'
    same_path = os.path.realpath(AGENT_REFS) == os.path.realpath(ref_dst)
    if not dry_run and not same_path:
        ref_dst.mkdir(parents=True, exist_ok=True)
        for f in AGENT_REFS.glob('*'):
            if f.is_dir():
                shutil.copytree(f, ref_dst / f.name, dirs_exist_ok=True)
            else:
                shutil.copy2(f, ref_dst / f.name)
    missing = [f.name for f in AGENT_REFS.iterdir() if f.is_file() and not (ref_dst / f.name).exists()]
    logs.append(f'agent-references: {"同路径跳过复制" if same_path else "已复制"} {len(list(AGENT_REFS.iterdir()))} 项' +
                (f' | 缺失: {missing}' if missing else ' | 全部在位'))

    # --- CLAUDE.md（不存在生成 / 存在 section 合并 / 纯自定义报 CONFLICT） ---
    md_path = project / 'CLAUDE.md'
    rendered = render_claude_md(name, book)
    if not md_path.exists():
        if not dry_run:
            md_path.write_text(rendered, encoding='utf-8')
        logs.append('CLAUDE.md: 已生成（占位符替换）')
    else:
        existing = md_path.read_text(encoding='utf-8')
        if SECTION_RE.search(existing):
            if not dry_run:
                md_path.write_text(merge_claude_md(existing, rendered), encoding='utf-8')
            logs.append('CLAUDE.md: 已按 section 合并（模板覆盖同名，用户独有保留）')
        else:
            logs.append('CLAUDE.md: CONFLICT 无 ## section，未覆盖（交由 AI 按合并策略处理）')

    # --- settings.local.json（复用 merge helper） ---
    settings_path = project / '.claude' / 'settings.local.json'
    if not dry_run:
        pybin = find_python()
        if pybin is None:
            logs.append('settings: FAIL 未找到 python 解释器，跳过（不可手写简化）')
        else:
            cmd = [pybin, str(MERGE_HELPER), '--existing', str(settings_path),
                   '--template', str(TEMPLATES / 'settings-hooks.json'),
                   '--output', str(settings_path)]
            r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
            if r.returncode != 0:
                logs.append(f'settings: FAIL merge helper exit={r.returncode} {r.stderr[-200:]}')
            else:
                try:
                    json.loads(settings_path.read_text(encoding='utf-8'))
                    logs.append('settings: 已合并（merge-claude-settings.py），JSON 有效')
                except json.JSONDecodeError as e:
                    logs.append(f'settings: FAIL JSON 无效 {e}')
    else:
        logs.append('settings: (dry-run 不执行 merge)')

    # --- sentinel + restart 标记 ---
    if not dry_run:
        sentinel = project / '.story-deployed'
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
    return logs


def verify(project: Path) -> list[str]:
    checks: list[str] = []
    ok = True

    def check(name: str, cond: bool, detail: str = ''):
        nonlocal ok
        checks.append(f'{"PASS" if cond else "FAIL"}  {name}  {detail}')
        if not cond:
            ok = False

    hooks = project / '.claude' / 'hooks'
    check('hooks 顶层脚本可执行', all(
        (hooks / f).is_file() and os.access(hooks / f, os.X_OK)
        for f in ('session-start.sh', 'session-end.sh', 'detect-story-gaps.sh',
                  'validate-story-commit.sh', 'guard-outline-before-prose.sh',
                  'check-prose-after-write.sh', 'pre-compact.sh', 'post-compact.sh')))
    check('hooks lib 在位', (hooks / 'lib' / 'common.sh').is_file() and (hooks / 'lib' / 'sentinel.sh').is_file())
    rules = project / '.claude' / 'rules'
    rules_ok = all(f.is_file() and 'paths:' in f.read_text(encoding='utf-8', errors='ignore')
                   for f in rules.glob('*.md'))
    check('rules 含 paths frontmatter', rules_ok)
    agents = project / '.claude' / 'agents'
    check('agents 7 个', len(list(agents.glob('*.md'))) == 7)
    ref_dst = project / '.claude' / 'skills' / 'moshu-setup' / 'references' / 'agent-references'
    same_path = os.path.realpath(AGENT_REFS) == os.path.realpath(ref_dst)
    ref_ok = same_path or all((ref_dst / f.name).exists() for f in AGENT_REFS.iterdir() if f.is_file())
    check('agent-references 在位', ref_ok)
    settings = project / '.claude' / 'settings.local.json'
    try:
        d = json.loads(settings.read_text(encoding='utf-8'))
        cmds = [h.get('command', '') for evt, blocks in d.get('hooks', {}).items()
                for b in blocks for h in b.get('hooks', [])]
        dup = {c for c in cmds if cmds.count(c) > 1}
        check('settings JSON 有效且命令无重复', bool(d) and not dup)
    except Exception as e:
        check('settings JSON 有效', False, str(e))
    sentinel = project / '.story-deployed'
    fields = ('deployed_at', 'agents_version', 'setup_skill_version', 'target_cli',
              'resolver_strategy', 'references_dir')
    check('sentinel 6 字段', sentinel.is_file() and all(
        re.search(rf'^{k}:', sentinel.read_text(encoding='utf-8'), re.M) for k in fields))
    checks.append('RESULT: ' + ('ALL PASS' if ok else 'HAS FAILURE'))
    return checks


def main():
    ap = argparse.ArgumentParser(description='moshu-setup 一键部署器')
    sub = ap.add_subparsers(dest='cmd', required=True)
    d = sub.add_parser('deploy', help='执行完整部署')
    d.add_argument('--project', required=True)
    d.add_argument('--name', required=True, help='项目名（CLAUDE.md 占位符）')
    d.add_argument('--book', default=None, help='书名（缺省=项目名）')
    d.add_argument('--agents-version', default='26')
    d.add_argument('--setup-version', default='1.2.9')
    d.add_argument('--dry-run', action='store_true')
    v = sub.add_parser('verify', help='Phase 3 验证')
    v.add_argument('--project', required=True)
    args = ap.parse_args()

    project = Path(args.project).resolve()
    if not project.is_dir():
        print(f'[错误] 项目目录不存在: {project}', file=sys.stderr)
        sys.exit(2)

    if args.cmd == 'deploy':
        logs = deploy(project, args.name, args.book or args.name,
                      args.agents_version, args.setup_version, args.dry_run)
        for line in logs:
            print(' -', line)
    else:
        for line in verify(project):
            print(line)


if __name__ == '__main__':
    main()
