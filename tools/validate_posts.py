#!/usr/bin/env python3
"""Validate publication queue without contacting Telegram or touching VPS."""
import json
import re
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
data=json.loads((ROOT/"posts.json").read_text(encoding="utf-8"))
posts=data["posts"]
assert isinstance(posts,list) and posts,"No posts"
seen=set()
for post in posts:
    ident=post["id"]
    assert isinstance(ident,str) and re.fullmatch(r"[A-Za-z0-9_-]{1,100}",ident),ident
    assert ident not in seen,ident
    seen.add(ident)
    dt=datetime.strptime(post["at"],"%Y-%m-%d %H:%M")
    assert 2020 <= dt.year <= 2100,ident
    if post.get("type")=="poll":
        assert isinstance(post.get("question"),str) and 1<=len(post["question"])<=300,ident
        assert 2<=len(post.get("options",[]))<=12,ident
        assert all(isinstance(x,str) and 1<=len(x)<=100 for x in post["options"]),ident
    else:
        text=post.get("text")
        assert isinstance(text,str) and 1<=len(text)<=4096,ident
        image=post.get("image")
        if image is not None:
            assert isinstance(image,str) and re.fullmatch(r"[A-Za-z0-9._-]{1,80}",image),ident
            asset=ROOT/image
            assert asset.is_file(),f"Missing image: {image}"
            assert asset.stat().st_size<=10_000_000,ident
            if len(text)>1024:
                print(f"INFO {ident}: long text will be sent as a separate Telegram message")
assert len(seen)==len(posts)
print(f"OK: {len(posts)} posts validated; channel queue is structurally valid.")
