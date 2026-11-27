# Checking Inn for Christmas: tune-in clip plan

Premiere: **Sat., Nov. 28 at 10/9c on Lifetime** (TV-PG). Every clip is a tune-in ad.

## Render

```bash
python3 clips/make_cards.py   # end cards + covers from the key art (once)
python3 clips/make_clip.py clips/specs/clip1.json --post-at 2026-11-28T13:00
```

`--post-at` is the time you'll **post**, in ET. The CTA switches on its own:
before Sat → "premieres Sat., Nov. 28 at 10/9c"; Sat before 10pm ET → "TONIGHT at 10/9c";
after → "Streaming now on Lifetime". Re-render Friday clips before reposting them on Saturday.

What it outputs: 1080x1920 H.264/AAC, original movie audio, burned-in hook (first 3 s) +
captions + CTA banner (last 4 s + end card), 2.5 s key-art end card. It refuses anything
outside 15-60 s. Use `fit: "blur"` for two-shots and `fit: "crop"` + `crop_x` for close-ups.

## Picking scenes (from the Frame.io footage only)

- 20-45 s of scene, one moment, cut **mid-tension**: the almost-kiss, the unanswered
  question, the reveal the camera is about to show. Never resolve it, never show the ending.
- Lead with the strongest beat in second 0-1. Trim lead-in dialogue.
- Three clips, three different scenes and hooks per account. No long chunks of the film.

| # | Scene type | On-screen hook | Cut point |
|---|---|---|---|
| 1 | Vivica / Jackée banter | "Vivica A. Fox + Jackée Harry in a Christmas movie? I'm seated 🎄" | right before the comeback lands |
| 2 | Claire arrives at the inn / meets Josh Henderson | "POV: your Thanksgiving weekend plans just changed" | the first lingering look, before either speaks |
| 3 | Romance beat (almost-kiss / confession) | "Lifetime Christmas movie season is officially here. Would you have said yes?" | the lean-in, before the kiss or the interruption |
| alt | Amelia gives Claire the assignment | "Who else watches every Lifetime Christmas movie? 🙋‍♀️" | Claire's answer, before she gives it |

## Captions (paste-ready; swap the first line per clip)

**TikTok**
> Would you check in? 🎄🏨 Checking Inn for Christmas premieres Sat., Nov. 28 at 10/9c on Lifetime @officiallifetimetv #CheckingInnForChristmas #ItsAWonderfulLifetime #Lifetime #ChristmasMovies #HolidayRomance #VivicaAFox

**Instagram / Facebook / X**
> Would you check in? 🎄🏨 Checking Inn for Christmas premieres Sat., Nov. 28 at 10/9c on Lifetime @lifetimetv #CheckingInnForChristmas #ItsAWonderfulLifetime #Lifetime #ChristmasMovies #HolidayRomance #VivicaAFox

On Saturday, swap in "premieres TONIGHT at 10/9c on Lifetime". After the premiere, use "Streaming now on Lifetime".

Question lines for comments: "Team Vivica or Team Jackée? 👇" · "Would you have taken the assignment?" · "What happens next? Wrong answers only 👇" · "How many Lifetime Christmas movies have you watched this year?"

## Posting schedule (ET)

| When | What |
|---|---|
| Fri Nov 27, as soon as rendered | Clip 1 on every account |
| Fri Nov 27, 7-9 pm | Clip 2 |
| Sat Nov 28, 11 am-1 pm | Clip 3, with the TONIGHT CTA |
| Sat Nov 28, 5-7 pm | Any clip re-cut with a new hook and the TONIGHT CTA. Pin a "starts in 3 hours" comment |
| Sun Nov 29 onward | Re-render with "Streaming now on Lifetime" |

## Compliance checklist

- [ ] Only Frame.io footage plus official key art and logo. No AI or altered footage of the actors
- [ ] TV-PG and festive. No ending spoilers. Cuts on a cliffhanger
- [ ] CTA on screen and in the caption. Lifetime tagged. All six hashtags present
- [ ] 15-60 s, 9:16, captions burned in, original sound
- [ ] Organic growth only: no bought views, engagement pods, or view bots
- [ ] Original edit. Don't repost another clipper's video
