"""Recover abandoned import writes without deleting registered or user files."""

import os
import time
from uuid import uuid4

from auto_tool_video.assets_gc import collect_garbage
from auto_tool_video.store import Store


def test_worker_startup_sweep_reclaims_only_expired_unregistered_assets(tmp_path):
    store = Store(tmp_path)
    directory = store.root / "assets"
    stale = directory / f"{uuid4()}.png"
    fresh = directory / f"{uuid4()}.jpg"
    user_file = directory / "my-personal-artwork.png"
    exported = store.root / "exports" / f"{uuid4()}.mp4"
    for path in (stale, fresh, user_file, exported):
        path.write_bytes(b"orphan test")
    old = time.time() - 2 * 86400
    os.utime(stale, (old, old))
    os.utime(user_file, (old, old))
    os.utime(exported, (old, old))
    report = collect_garbage(store)
    assert report["deleted"] == 1
    assert not stale.exists()
    assert fresh.exists()
    assert user_file.exists()
    assert exported.exists()


def test_startup_sweep_never_unlinks_symlinks_or_targets(tmp_path):
    store = Store(tmp_path)
    target = tmp_path / "private.png"
    target.write_bytes(b"private")
    alias = store.root / "assets" / f"{uuid4()}.png"
    alias.symlink_to(target)
    assert collect_garbage(store)["deleted"] == 0
    assert alias.is_symlink()
    assert target.read_bytes() == b"private"
