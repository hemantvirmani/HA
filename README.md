# Home Assistant Dashboard

Home Assistant Lovelace dashboard configuration managed in YAML mode.

## 📁 Files

| File | Purpose |
|------|---------|
| `current-dashboard.yaml` | Active working dashboard (edit this file) |
| `old.dashboard.yaml` | Frozen Snapshot - Original production dashboard (do not modify) |
| `new.dashboard.yaml` | Frozen Snapshot - Snapshot used to create current-dashboard (do not modify) |
| `deploy_dashboard.py` | Deployment script for pushing changes to HA |

## 🏷️ Tagging / Checkpoints

| Tag | Points To | Description |
|-----|-----------|-------------|
| `dashboard-v1` | First commit | Original dashboard (`old.dashboard.yaml`) |
| `dashboard-v2` | Current | New dashboard with inline styles, teal backgrounds, section headers |
| `live-v1` | Same as v2 | First live deployment |

**Usage:**
- Compare versions: `git diff dashboard-v1 dashboard-v2 -- current-dashboard.yaml`
- View a past version: `git show dashboard-v2:current-dashboard.yaml`
- Tag a new checkpoint: `git tag -a dashboard-v3 -m "description"`
- Tag a live deploy: `git tag -a live-v2 -m "description"`

## 🔧 Development Workflow

1. Edit `current-dashboard.yaml` locally
2. Validate YAML syntax
3. Deploy with `deploy_dashboard.py` (see [DEPLOYMENT.md](DEPLOYMENT.md) for details)
4. Verify in Home Assistant UI
5. Tag checkpoint: `git tag -a dashboard-vN -m "description"`
6. If deploying live: `git tag -a live-vN -m "description"`

## 🚀 Quick Deploy

```bash
# Deploy to Home Assistant
python deploy_dashboard.py --host YOUR_HA_IP --user root --key ~/.ssh/id_rsa
```

> **Need detailed setup instructions?** See [DEPLOYMENT.md](DEPLOYMENT.md) for venv setup, SSH configuration, and troubleshooting.

## 📚 Documentation

- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Complete deployment guide with troubleshooting
- **[.clinerules](.clinerules)** - Coding conventions and best practices for Cline

## 🎨 Dashboard Views

The dashboard contains five views:

1. **Home** - Greeting, weather alerts, light controls, device status, battery monitoring, weather graphs
2. **Security** - Ring alarm panel, CO/smoke sensors, motion detectors, door/window contacts, camera feeds
3. **Devices** - Vacuum cleaners, printer status, WiFi router stats, sprinkler controls, unavailable entities
4. **Watchtower** - Temperature/humidity charts, hardware monitoring (CPU, memory, disk), air pollution gauges
5. **Extras** - Person tracking (location, battery, steps, connectivity) for family members

## 🎨 Custom Cards Used

- **Mushroom Cards:** template, entity, person, vacuum, chips
- **Bubble Cards:** button, climate, media-player, pop-up
- **Other:** mini-graph-card, apexcharts-card, clock-weather-card, horizon-card, auto-entities, stack-in-card
- **Styling:** card_mod for CSS overrides

## 🎨 Style Architecture

YAML anchors are defined once at the top level in `_styles:` section and reused throughout:

| Anchor | Color | Usage |
|--------|-------|--------|
| `*style_section_header` | `rgba(29, 78, 216, 0.95)` | Blue section headings |
| `*style_section_header_hidden` | `rgba(29, 78, 216, 0.95)` + `display: none` | Hidden section headers |
| `*style_teal` | `rgb(45, 95, 125)` | Teal content/data cards |
| `*style_teal_hidden` | `rgb(45, 95, 125)` + `display: none` | Teal cards hidden from view (swap to `*style_teal` to show) |
| `*style_greeting` | `rgba(2, 132, 199, 0.95)` | Greeting banner |
| `*style_alert_red` | `rgb(220, 53, 69)` | Weather alert cards |
| `*style_alert_red_alpha` | `rgba(220, 53, 69, 0.95)` | Weather alert detail cards |
| `*style_thermostat_popup` | `rgb(37, 85, 178)` | Thermostat popup |

### Bubble Card CSS Variables

CSS custom properties for bubble-card are defined inline in each card's `:host` block (inside the card's shadow DOM). Bubble-card does not inherit CSS variables from view-level `card_mod` or theme files.

**Button cards:**

| Property | Value | Effect |
|----------|-------|--------|
| `--bubble-button-border-radius` | `7px` | Rounded corners on bubble buttons |
| `--bubble-sub-button-border-radius` | `7px` | Rounded corners on bubble sub-buttons |
| `--bubble-button-bg` | `rgba(52, 152, 220, 0.95)` | Bubble button background color |
| `--bubble-icon-container-bg` | `#0F2C64` | Bubble icon container (dark blue) |
| `--bubble-sub-icon-size` | `13px` | Sub-button icon size |

**Climate / media-player cards:**

| Property | Value | Effect |
|----------|-------|--------|
| `--bubble-border-radius` | `7px` | Card border radius (not button-specific) |
| `--bubble-sub-button-border-radius` | `7px` | Rounded corners on sub-buttons |
| `--bubble-icon-container-black` | `black` | Icon container for climate/media cards |
| `--bubble-sub-icon-size` | `13px` | Sub-button icon size |

Each bubble card's `styles:` uses `var(--variable)` to reference these values from its own `:host` block.

## 📖 More Information

- Home Assistant: https://www.home-assistant.io/
- Lovelace Documentation: https://www.home-assistant.io/lovelace/
- Deployment Guide: [DEPLOYMENT.md](DEPLOYMENT.md)
