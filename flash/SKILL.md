---
name: timepoint-flash
description: Generate rich historical timepoints with text and images using the Timepoint Flash API
version: 1.0.0
author: Timepoint AI
metadata:
  hermes:
    tags: [history, generation, flash, timepoint, images]
    related_skills: [timepoint-clockchain]
---

# Timepoint Flash

Flash is the generation engine for the Timepoint ecosystem. It creates rich historical "timepoints" — narrative scenes with characters, dialog, atmosphere, and images.

## Setup

Flash is **open source** — you can clone and run your own instance:

```bash
git clone https://github.com/timepointai/timepoint-flash.git
```

Point `FLASH_API_URL` at your instance. No API key needed for self-hosted.

Or use the hosted version at `flash.timepointai.com` with an `X-Service-Key` header for authentication.

## Key Endpoints

### Generate a Timepoint
```
POST /api/v1/timepoints/generate
Content-Type: application/json
X-Service-Key: <your-service-key>

{
  "query": "The signing of the Magna Carta at Runnymede, 1215",
  "preset": "free_distillable",
  "model_policy": "permissive"
}
```

Returns a full timepoint with narrative, characters, dialog, and metadata.

### Presets
- **free_distillable**: Zero cost, text-only, uses Hunter Alpha / Healer Alpha
- **balanced**: Good quality/speed balance (uses Google Gemini)
- **hd**: Highest quality with images (uses Gemini + Nano Banana Pro)
- **hyper**: Fastest generation

### List Available Models
```
GET /api/v1/models
GET /api/v1/models/free
```

## Integration with Clockchain

When Flash generates a timepoint, it can be proposed to the Clockchain:
1. Generate a timepoint with Flash (rich narrative + metadata)
2. Extract the key facts (year, location, figures, causal connections)
3. Use `propose_moment` on the Clockchain MCP to add it to the graph
4. The Clockchain tracks provenance (which model generated it, which agent proposed it)

## Usage Notes

- Use `preset=free_distillable` for zero-cost text generation
- Use `model_policy=permissive` to ensure only open-weight models are used
- Flash handles the narrative generation; Clockchain handles the graph structure
- You can generate without images by using the free_distillable preset
