---
name: meeting-sim
description: Simulate upcoming meetings using Timepoint Flash — generates narrative previews with images showing what your next meeting might look like
version: 1.0.0
author: Timepoint AI
metadata:
  hermes:
    tags: [meetings, simulation, flash, calendar, preview, images]
    related_skills: [timepoint-flash, timepoint-clockchain]
---

# Meeting Simulator

Simulate upcoming meetings by generating rich narrative previews with images using Timepoint Flash. Pulls meetings from Cal.com or Google Calendar, then renders each one as an immersive "future timepoint" — complete with characters, likely dialog, atmosphere, and a generated image.

## Quick Start

Run the helper script to simulate your next meeting:

```bash
python /root/.hermes/skills/meeting-sim/sim.py --next
```

Or simulate all meetings in the next 24 hours:

```bash
python /root/.hermes/skills/meeting-sim/sim.py --hours 24
```

Or simulate a specific meeting by description:

```bash
python /root/.hermes/skills/meeting-sim/sim.py --query "Q2 roadmap planning with engineering team, 4 people, Tuesday 2pm"
```

## How It Works

1. **Fetch meetings** from Cal.com API (`GET /v2/bookings?status=upcoming`)
2. **Build a simulation prompt** for each meeting: attendees, title, context, time/location
3. **Call Flash** (`POST /api/v1/timepoints/generate/sync`) with `preset=balanced` and `generate_image=true`
4. **Return** a rich preview: narrative scene, characters, likely dialog, key discussion points, and an image

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `CALCOM_API_KEY` | Yes (for calendar) | Cal.com API key from Settings > Security |
| `FLASH_API_URL` | Yes | Flash API base URL |
| `FLASH_SERVICE_KEY` | Yes | Flash service authentication key |
| `CALCOM_API_URL` | No | Cal.com API base (default: `https://api.cal.com`) |

## Output Format

The simulator returns a JSON object per meeting:

```json
{
  "meeting": {
    "title": "Q2 Roadmap Review",
    "start": "2026-03-17T14:00:00Z",
    "attendees": ["Sean McDonald", "Jane Doe"],
    "location": "Google Meet"
  },
  "simulation": {
    "narrative": "The meeting opens with tension...",
    "characters": [...],
    "dialog": [...],
    "scene": { "setting": "...", "atmosphere": "..." },
    "image_url": "https://...",
    "key_topics": ["budget allocation", "hiring timeline"],
    "predicted_outcomes": ["Agreement on Q2 priorities", "Action items assigned"]
  }
}
```

## Usage Tips

- Use `--preset hd` for highest quality images (slower, ~30s)
- Use `--preset balanced` for good quality + speed (default, ~15s)
- Use `--no-image` to skip image generation (faster, text-only)
- Use `--query` to simulate a hypothetical meeting without calendar access
- The agent can run this on a cron schedule to deliver morning meeting previews

## Integration with Clockchain

For richer simulations, the agent can query the Clockchain for context:
- Past meetings with the same attendees (if stored as moments)
- Historical precedents for the topics being discussed
- Causal chains that led to this meeting happening

## Cron Example

Deliver morning meeting previews at 7am:

```
hermes cron create "0 7 * * *" "Run /meeting-sim --hours 12 and summarize the previews" --name "morning-meetings" --deliver telegram
```
