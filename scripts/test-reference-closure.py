#!/usr/bin/env python3
"""引用闭包守卫回归（方案 A 资产宇宙）。

守护对象：check-reference-closure.py 的「提及文件名 ∈ 资产宇宙才做闭包断言 / 非资产忽略 / 白名单带理由」语义。
禁：断言实现细节/真实上游/脆弱快照（scripts/README.md 测试纪律）。批B4 勘误 §4 五用例。
"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
GUARD = REPO_ROOT / "scripts" / "check-reference-closure.py"


def _load_guard_module():
    spec = importlib.util.spec_from_file_location("cref_closure_under_test", GUARD)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


guard = _load_guard_module()
fails = 0


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _make_fixture() -> tuple[tempfile.TemporaryDirectory, Path]:
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name)
    # skillA：本域有 exists.md；doc.md 提及四类（本域存在/宇宙内本域缺失/白名单内/非资产运行态）。
    _write(root / "skills/skillA/references/exists.md", "# exists\n")
    _write(
        root / "skills/skillA/references/doc.md",
        "# doc\n"
        "本域资产：`exists.md`。\n"
        "宇宙内本域缺失：`missing-asset.md`。\n"
        "白名单内：`whitelisted.md`。\n"
        "非资产运行态：`题材定位.md`。\n",
    )
    # 使 missing-asset.md / whitelisted.md 进入资产宇宙（其它 skill 的 references 直接子项）。
    _write(root / "skills/skillB/references/whitelisted.md", "# whitelisted\n")
    _write(root / "skills/skillC/references/missing-asset.md", "# missing\n")
    return tmp, root


def _mention(failure: str) -> str:
    return failure.rsplit(":", 1)[-1]


def _has(failures: list[str], name: str) -> bool:
    return any(_mention(f) == name for f in failures)


def run() -> None:
    global fails
    tmp, root = _make_fixture()
    try:
        # ① 提及本域存在文件 → 过
        failures, _ = guard.check(root)
        if _has(failures, "exists.md"):
            print("FAIL: ① 本域存在的提及不应报")
            fails += 1

        # ② 资产宇宙内但本域缺失 → 违规且报文含文件名
        if not _has(failures, "missing-asset.md"):
            print("FAIL: ② 资产宇宙内本域缺失应报 missing-asset.md")
            fails += 1

        # ⑤ 提及 ∉ 资产宇宙的运行态产物名 → 忽略不报
        if _has(failures, "题材定位.md"):
            print("FAIL: ⑤ 非资产宇宙运行态产物不应报")
            fails += 1

        # ③ 白名单内提及 → 过；④ 移除白名单后 → 违规
        original_whitelist = dict(guard.ALLOWED_CROSS_DOMAIN)
        try:
            guard.ALLOWED_CROSS_DOMAIN["whitelisted.md"] = "测试：白名单机制生效"
            failures, _ = guard.check(root)
            if _has(failures, "whitelisted.md"):
                print("FAIL: ③ 白名单内提及应过")
                fails += 1
            del guard.ALLOWED_CROSS_DOMAIN["whitelisted.md"]
            failures, _ = guard.check(root)
            if not _has(failures, "whitelisted.md"):
                print("FAIL: ④ 移除白名单后应违规")
                fails += 1
        finally:
            guard.ALLOWED_CROSS_DOMAIN = original_whitelist
    finally:
        tmp.cleanup()


def main() -> int:
    run()
    if fails:
        print(f"Reference-closure tests FAILED ({fails}).")
        return 1
    print("Reference-closure regression tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
