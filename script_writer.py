"""Write script from validated topic. Channel-aware: facts vs Hindi meme skits."""
import json
from claude_cli import ask_json


def write_script(topic: dict, channel: dict) -> dict:
    if channel["script_rules"] == "memes":
        prompt = f"""You are the admin of a viral Indian meme page. Write a 12-second Hindi comedy skit.
Scenario: {topic['topic']} | Punchline: {topic['hook']}
HOOK RULE: segment 1 starts MID-CHAOS — most absurd moment first, explain later.
RULES: 3-4 segments, MAX 9 Hindi words per segment, MAX 34 words total. Count them.
Hinglish flavor (bhai, yaar, arre). NO explaining the joke. End ON the punchline.
text = 100% Hindi Devanagari (for hi-IN TTS). display_text = short Hinglish caption (max 6 words).
sound_cue: vine-boom / aayein / dramatic / slap / laugh / cricket / run / wow / fail / none

JSON: {{"segments":[{{"text":"हिंदी","display_text":"hinglish caption","duration_s":3,"sound_cue":"..."}}],
"title":"Hinglish title 😂 max 60 chars","description":"1-2 funny lines + follow CTA",
"hashtags":["#memes","#funny","#Shorts","#desimemes"]}}"""
    else:
        prompt = f"""Viral YouTube Shorts scriptwriter. Write a punchy Did-You-Know Short.
Topic: {topic['topic']} | Hook: {topic['hook']} | Fact: {topic.get('fact_summary','')}
RULES: 16-19s MAX (~40-48 words). First sentence = question/pattern-interrupt.
4-5 segments, each 3-5s. Max 10 words/sentence. Concrete numbers.
JSON: {{"segments":[{{"text":"...","display_text":"SHORT max 8 words","duration_s":3}}],
"title":"YouTube title max 60 chars","description":"2-3 sentences + subscribe CTA",
"hashtags":["#DidYouKnow","#Facts","#Shorts"]}}"""

    script = ask_json(prompt)

    # word-budget enforcement for memes
    if channel["script_rules"] == "memes":
        total_words = sum(len(s.get("text","").split()) for s in script.get("segments",[]))
        if total_words > 40:
            print(f"   ⚠️ script too long ({total_words} words) — compressing")
            script = ask_json(
                f"Rewrite to MAX 34 total Hindi words, keep mid-chaos hook and punchline twist. "
                f"Same JSON structure. JSON only:\n{json.dumps(script, ensure_ascii=False)}"
            )

    script["topic"] = topic["topic"]
    script["hook"]  = topic["hook"]
    return script
