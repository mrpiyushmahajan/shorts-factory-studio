"""Research + validate topics. Channel-aware: facts vs meme skits."""
from claude_cli import ask_json


def _load_recent(channel: dict, n: int = 15) -> list[str]:
    ledger = channel["data_dir"] / "posts_ledger.md"
    if not ledger.exists():
        return []
    lines = ledger.read_text(encoding="utf-8").splitlines()
    return [l.replace("- Topic:", "").strip() for l in lines[-n:] if l.startswith("- Topic:")]


def generate_candidates(channel: dict, n: int = 8) -> list[dict]:
    avoid = "\n".join(f"- {t}" for t in _load_recent(channel)) or "(none yet)"
    if channel["script_rules"] == "memes":
        prompt = f"""You are a 5M-follower Indian meme page admin. Generate {n} FUNNY MEME SCENARIOS
for animated YouTube Shorts — cartoon skits of animals/humans in Indian everyday situations.
GROUP CHAT TEST: would a 19-year-old tag a friend with "😭😭"?
Each needs: ABSURD PREMISE + real PUNCHLINE TWIST + opens MID-CHAOS.
NOT similar to: {avoid}
JSON array, each: topic, hook (punchline), fact_summary (skit outline), virality_score (1-10), source_hint (Indian trope). JSON only."""
    else:
        prompt = f"""Viral YouTube Shorts producer for "{channel['niche']}". Target: {channel['audience']}.
Generate {n} surprising Did-You-Know topics — shocking, verifiable, explainable in 20s.
NOT similar to: {avoid}
JSON array, each: topic, hook, fact_summary, virality_score (1-10), source_hint. JSON only."""
    return ask_json(prompt)


def validate_topic(candidate: dict, channel: dict) -> dict:
    if channel["script_rules"] == "memes":
        axes = "surprise_factor, shareability, rewatch_value, broad_appeal, hook_strength"
        threshold = 40
        desc = "Indian meme comedy channel"
    else:
        axes = "surprise_factor, shareability, rewatch_value, broad_appeal, hook_strength"
        threshold = 35
        desc = "Did You Know facts channel"
    prompt = f"""Evaluate for a {desc}.
Topic: {candidate['topic']} | Hook: {candidate['hook']} | Content: {candidate.get('fact_summary','')}
Score 1-10 each: {axes}. Be RUTHLESS — cute/predictable = 4. PASS if total >= {threshold}.
JSON: {{"scores":{{"surprise_factor":0,"shareability":0,"rewatch_value":0,"broad_appeal":0,"hook_strength":0}},"total":0,"verdict":"PASS or FAIL","reason":"one sentence"}}"""
    return {**candidate, **ask_json(prompt)}


def pick_topic(channel: dict) -> dict:
    best, best_score = None, -1
    for round_no in range(2):
        print(f"🔍 Generating candidates (round {round_no+1})...")
        candidates = generate_candidates(channel, n=8)
        candidates.sort(key=lambda c: c.get("virality_score", 0), reverse=True)
        for c in candidates:
            print(f"   Testing: {c['topic']}")
            v = validate_topic(c, channel)
            total = v.get("total", 0)
            print(f"   → {v.get('verdict','FAIL')} ({total}/50): {v.get('reason','')}")
            if v.get("verdict") == "PASS":
                return v
            if total > best_score:
                best, best_score = v, total
    print(f"⚠️  Using best near-miss ({best_score}/50)")
    return best
