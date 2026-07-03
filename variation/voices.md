# Voice + length + pace pool (rotate — vary the narrator, duration, and pacing)

The producer picks a voice NOT used in the last ~4 videos, and rotates the length bucket + pace so videos
don't all sound identical. Pass the chosen voice/rate to `make_narration.py --voice <id> --rate <±n%>`.

## Voice pool (all confirmed on this box, edge-tts)
| id | Voice (edge-tts ShortName) | Character |
|---|---|---|
| V1 | en-US-AndrewMultilingualNeural | warm, conversational male (original default) |
| V2 | en-US-AriaNeural | energetic, expressive female |
| V3 | en-US-GuyNeural | crisp, authoritative male (news) |
| V4 | en-US-ChristopherNeural | deep, confident male |
| V5 | en-GB-RyanNeural | British male |
| V6 | en-GB-SoniaNeural | British female |
| V7 | en-AU-NatashaNeural | Australian female |
| V8 | en-US-EmmaNeural | friendly, upbeat female |

## Length buckets (rotate)
| id | Target | ~spoken words | Notes |
|---|---|---|---|
| L1 | ~15s | ~40 | punchy, single sharp idea (great for listicle/test-it) |
| L2 | ~25s | ~65 | tight explainer/myth-bust |
| L3 | ~35s | ~90 | fuller explainer/story (house default range) |
| L4 | ~45s | ~115 | deep case-study (only if it stays high-retention) |

## Pace (rotate slightly)
`--rate` in {`-8%`, `-4%`, `0%`, `+4%`, `+6%`}. Faster for listicle/test-it, slower for story/explainer.

**Rules:** don't reuse a voice within 4 videos; vary gender + accent across the week; pick length to fit
the format (listicle/test-it → L1/L2; story/case-study → L3/L4). Record voice+length+pace in `variation_ledger.md`.
