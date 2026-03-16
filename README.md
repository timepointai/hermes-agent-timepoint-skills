# Hermes Agent Timepoint Skills

[Hermes Agent](https://github.com/NousResearch/hermes-agent) skills for the [Timepoint](https://timepointai.com) ecosystem.

## Skills

| Skill | Description |
|-------|-------------|
| [clockchain](./clockchain/) | Query, propose, and challenge moments on the Clockchain temporal graph via MCP |
| [flash](./flash/) | Generate rich historical timepoints with text and images using Timepoint Flash |
| [meeting-sim](./meeting-sim/) | Simulate upcoming meetings with immersive previews, dialog, and AI-generated images |

## Install

```bash
hermes skills install github:timepointai/hermes-agent-timepoint-skills
```

Or install individual skills:

```bash
hermes skills install github:timepointai/hermes-agent-timepoint-skills/clockchain
hermes skills install github:timepointai/hermes-agent-timepoint-skills/flash
hermes skills install github:timepointai/hermes-agent-timepoint-skills/meeting-sim
```

## Requirements

### Clockchain
- MCP connection to a Clockchain instance (e.g. `clockchain.timepointai.com/mcp/`)
- Writer token for authenticated proposals

### Flash
- Flash API access (`flash.timepointai.com`)
- Service key (`FLASH_SERVICE_KEY`)

### Meeting Simulator
- Flash API access (for rendering)
- Cal.com API key (`CALCOM_API_KEY`) for calendar integration, **or**
- Google Calendar OAuth2 token (`GOOGLE_TOKEN_PATH`) for Google integration, **or**
- Use `--mock` for demo mode with realistic sample meetings (no API keys needed)
- Or use `--query` mode for freeform meeting simulation without calendar

## Usage

Once installed, skills are available as slash commands in Hermes:

```
/clockchain    — "Query the Clockchain for events related to the Renaissance"
/flash         — "Generate a timepoint for the moon landing"
/meeting-sim   — "Simulate my next meeting"
```

The meeting simulator can also run as a standalone script:

```bash
python meeting-sim/sim.py --next --mock             # Demo with mock calendar
python meeting-sim/sim.py --next --source google     # Google Calendar
python meeting-sim/sim.py --next                      # Cal.com (default)
python meeting-sim/sim.py --hours 24 --mock           # All mock meetings today
python meeting-sim/sim.py --query "Board meeting, CEO and 3 investors, Series A"
```

## Stack

```
Hermes Agent
  ├── MCP ──> Clockchain (propose/challenge/query moments)
  ├── HTTP ──> Flash (generate timepoints + images)
  └── HTTP ──> Cal.com (fetch upcoming meetings)
```

## License

MIT
