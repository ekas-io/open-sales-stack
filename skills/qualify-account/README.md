# Qualify Account Skills

Claude skills that research and qualify sales accounts. Each skill variant uses a different qualification framework — a set of signals tailored to a specific sales motion or ideal customer profile.

![Qualify Demo](../assets/qualify-demo.gif)


## Available Skills

| Skill | Tools | Description |
|-------|-------|-------------|
| [high-inbound-volume](./high-inbound-volume/) | Apollo | Qualifies accounts based on 5 inbound lead volume signals |

## Adding More Skills

The `qualify-account/` directory is organized by variant. Each variant lives in its own folder with:
- `setup.sh` — interactive setup script
- `skill-source/` — the skill template files
- `README.md` — documentation specific to that variant (prerequisites, setup, usage)
