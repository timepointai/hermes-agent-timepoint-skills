"""Meeting Simulator — render upcoming meetings as immersive Flash timepoints.

Fetches meetings from Cal.com, builds rich prompts, and calls Timepoint Flash
to generate narrative previews with images.

Usage:
    python sim.py --next                    # Simulate next meeting
    python sim.py --hours 24                # All meetings in next 24h
    python sim.py --query "Team standup..." # Simulate from description
    python sim.py --next --preset hd        # High-quality images
    python sim.py --next --no-image         # Text only (faster)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from urllib.request import Request, urlopen
from urllib.error import HTTPError

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

CALCOM_API_URL = os.environ.get("CALCOM_API_URL", "https://api.cal.com")
CALCOM_API_KEY = os.environ.get("CALCOM_API_KEY", "")
FLASH_API_URL = os.environ.get("FLASH_API_URL", "https://flash.timepointai.com")
FLASH_SERVICE_KEY = os.environ.get("FLASH_SERVICE_KEY", "")


def _api(method: str, url: str, headers: dict, body: dict | None = None, timeout: int = 60) -> dict:
    """Make an HTTP request and return parsed JSON."""
    data = json.dumps(body).encode() if body else None
    req = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except HTTPError as e:
        error_body = e.read().decode() if e.fp else ""
        print(f"HTTP {e.code} from {url}: {error_body}", file=sys.stderr)
        raise


# ---------------------------------------------------------------------------
# Calendar
# ---------------------------------------------------------------------------

def fetch_upcoming_meetings(hours_ahead: int = 24, limit: int = 10) -> list[dict]:
    """Fetch upcoming bookings from Cal.com v2 API."""
    if not CALCOM_API_KEY:
        print("CALCOM_API_KEY not set — cannot fetch calendar", file=sys.stderr)
        return []

    now = datetime.now(timezone.utc)
    end = now + timedelta(hours=hours_ahead)

    url = (
        f"{CALCOM_API_URL}/v2/bookings"
        f"?status=upcoming"
        f"&afterStart={now.strftime('%Y-%m-%dT%H:%M:%SZ')}"
        f"&beforeEnd={end.strftime('%Y-%m-%dT%H:%M:%SZ')}"
        f"&sortStart=asc"
        f"&take={limit}"
    )
    headers = {
        "Authorization": f"Bearer {CALCOM_API_KEY}",
        "cal-api-version": "2024-08-13",
        "Content-Type": "application/json",
    }
    resp = _api("GET", url, headers)
    return resp.get("data", [])


def meeting_to_prompt(meeting: dict) -> str:
    """Convert a Cal.com booking into a Flash generation prompt."""
    title = meeting.get("title", "Untitled Meeting")
    start = meeting.get("start", "")
    end = meeting.get("end", "")
    location = meeting.get("location", "Virtual")
    description = meeting.get("description", "")

    # Gather all people
    hosts = meeting.get("hosts", [])
    attendees = meeting.get("attendees", [])
    guests = meeting.get("guests", [])

    people = []
    for h in hosts:
        people.append(f"{h.get('name', 'Host')} (host)")
    for a in attendees:
        people.append(a.get("name", a.get("email", "Attendee")))
    for g in guests:
        people.append(g if isinstance(g, str) else str(g))

    people_str = ", ".join(people) if people else "Unknown attendees"

    # Parse time for natural language
    try:
        dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
        time_str = dt.strftime("%A, %B %d, %Y at %I:%M %p UTC")
    except (ValueError, AttributeError):
        time_str = start

    # Duration
    duration = meeting.get("duration", "")
    dur_str = f" ({duration} minutes)" if duration else ""

    prompt = (
        f"Simulate this upcoming meeting as a vivid, immersive scene:\n\n"
        f"MEETING: {title}\n"
        f"WHEN: {time_str}{dur_str}\n"
        f"WHERE: {location}\n"
        f"PARTICIPANTS: {people_str}\n"
    )
    if description:
        prompt += f"CONTEXT: {description}\n"

    prompt += (
        f"\nRender this as a future moment — show the room/space, the people arriving, "
        f"the opening exchanges, the key discussion points, moments of tension or "
        f"agreement, and how the meeting concludes. Include likely dialog based on "
        f"the meeting topic. Make it feel real and specific, like a scene from a film. "
        f"The image should capture the pivotal moment of the meeting."
    )
    return prompt


# ---------------------------------------------------------------------------
# Flash
# ---------------------------------------------------------------------------

def simulate_meeting(
    prompt: str,
    preset: str = "balanced",
    generate_image: bool = True,
) -> dict:
    """Call Flash to generate a meeting simulation timepoint (async + poll)."""
    if not FLASH_SERVICE_KEY:
        print("FLASH_SERVICE_KEY not set — cannot generate", file=sys.stderr)
        return {"error": "FLASH_SERVICE_KEY not set"}

    headers = {
        "X-Service-Key": FLASH_SERVICE_KEY,
        "Content-Type": "application/json",
    }
    body = {
        "query": prompt[:500],  # Flash limit
        "preset": preset,
        "generate_image": generate_image,
        "request_context": {
            "source": "meeting-sim",
            "agent": "timepoint-hermes-agent-1",
        },
    }

    print(f"  Generating with Flash ({preset}, image={'yes' if generate_image else 'no'})...")
    print(f"  This may take 2-3 minutes...")

    # Use sync endpoint — returns full structured response inline.
    # The GET endpoint doesn't return characters/dialog/scene fields.
    sync_url = f"{FLASH_API_URL}/api/v1/timepoints/generate/sync"
    resp = _api("POST", sync_url, headers, body, timeout=300)

    if resp.get("status") == "failed":
        err = resp.get("error", "unknown error")
        print(f"  Flash generation failed: {err}", file=sys.stderr)
        return {"error": err}

    gen_time = resp.get("generation_time_ms", 0)
    print(f"  Done ({gen_time / 1000:.0f}s)")
    return resp


def format_simulation(meeting: dict | None, sim: dict) -> dict:
    """Format the simulation output."""
    result = {}

    if meeting:
        result["meeting"] = {
            "title": meeting.get("title", ""),
            "start": meeting.get("start", ""),
            "end": meeting.get("end", ""),
            "attendees": [
                a.get("name", a.get("email", ""))
                for a in meeting.get("attendees", [])
            ] + [
                h.get("name", "") for h in meeting.get("hosts", [])
            ],
            "location": meeting.get("location", ""),
        }

    result["simulation"] = {
        "narrative": sim.get("moment", {}).get("narrative", ""),
        "significance": sim.get("moment", {}).get("significance", ""),
        "characters": sim.get("characters", {}).get("characters", []),
        "dialog": sim.get("dialog", []),
        "scene": sim.get("scene", {}),
        "image_url": sim.get("image_url"),
        "has_image": sim.get("has_image", False),
        "preset_used": sim.get("preset_used", ""),
        "generation_time_ms": sim.get("generation_time_ms"),
        "tags": sim.get("tags", []),
    }

    return result


def print_simulation(result: dict) -> None:
    """Pretty-print a simulation result."""
    meeting = result.get("meeting", {})
    sim = result.get("simulation", {})

    print("\n" + "=" * 60)
    if meeting:
        print(f"MEETING: {meeting.get('title', 'Unknown')}")
        print(f"  When: {meeting.get('start', '?')}")
        print(f"  Who:  {', '.join(meeting.get('attendees', []))}")
        print(f"  Where: {meeting.get('location', '?')}")
    print("=" * 60)

    if sim.get("narrative"):
        print(f"\nNARRATIVE:\n{sim['narrative']}")

    if sim.get("scene"):
        scene = sim["scene"]
        if scene.get("setting"):
            print(f"\nSETTING: {scene['setting']}")
        if scene.get("atmosphere"):
            print(f"ATMOSPHERE: {scene['atmosphere']}")

    if sim.get("dialog"):
        print("\nDIALOG:")
        for line in sim["dialog"][:8]:
            speaker = line.get("speaker", "?")
            text = line.get("text", "")
            emotion = line.get("emotion", "")
            em = f" [{emotion}]" if emotion else ""
            print(f"  {speaker}{em}: \"{text}\"")

    if sim.get("characters"):
        print("\nCHARACTERS:")
        for c in sim["characters"][:6]:
            print(f"  - {c.get('name', '?')}: {c.get('role', '')} — {c.get('bio', '')[:80]}")

    if sim.get("image_url"):
        print(f"\nIMAGE: {sim['image_url']}")

    if sim.get("generation_time_ms"):
        print(f"\n(Generated in {sim['generation_time_ms'] / 1000:.1f}s with {sim.get('preset_used', '?')} preset)")

    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Simulate upcoming meetings with Timepoint Flash")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--next", action="store_true", help="Simulate the next upcoming meeting")
    group.add_argument("--hours", type=int, help="Simulate all meetings in the next N hours")
    group.add_argument("--query", type=str, help="Simulate a meeting from a text description")

    parser.add_argument("--preset", default="balanced", choices=["balanced", "hd", "hyper", "gemini3"],
                        help="Flash quality preset (default: balanced)")
    parser.add_argument("--no-image", action="store_true", help="Skip image generation")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")

    args = parser.parse_args()
    generate_image = not args.no_image
    results = []

    if args.query:
        # Simulate from text description
        prompt = (
            f"Simulate this upcoming meeting as a vivid, immersive scene:\n\n"
            f"{args.query}\n\n"
            f"Render this as a future moment — show the room/space, the people arriving, "
            f"the opening exchanges, the key discussion points, moments of tension or "
            f"agreement, and how the meeting concludes. Include likely dialog. "
            f"Make it feel real and specific. The image should capture the pivotal moment."
        )
        sim = simulate_meeting(prompt, args.preset, generate_image)
        if not sim.get("error"):
            result = format_simulation(None, sim)
            results.append(result)

    else:
        # Fetch from calendar
        hours = 1 if args.next else args.hours
        limit = 1 if args.next else 10
        meetings = fetch_upcoming_meetings(hours_ahead=hours or 24, limit=limit)

        if not meetings:
            if CALCOM_API_KEY:
                print("No upcoming meetings found in the specified window.")
            else:
                print("No CALCOM_API_KEY set. Use --query to simulate without calendar access.")
            return

        for i, meeting in enumerate(meetings):
            title = meeting.get("title", "Meeting")
            print(f"\n[{i + 1}/{len(meetings)}] Simulating: {title}")
            prompt = meeting_to_prompt(meeting)
            sim = simulate_meeting(prompt, args.preset, generate_image)
            if not sim.get("error"):
                result = format_simulation(meeting, sim)
                results.append(result)

    # Output
    if args.json:
        print(json.dumps(results, indent=2, default=str))
    else:
        for r in results:
            print_simulation(r)

    if not results:
        print("No simulations generated.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
