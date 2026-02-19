# Home Assistant Dashboard

Home Assistant Lovelace dashboard configuration managed in YAML mode.

## 📁 Project Structure

```
HA/
├── my-dashboard.yaml           # Main dashboard configuration (edit this file)
├── themes/                    # Theme resources
│   ├── bg.png                 # Dashboard background image
│   └── my_dashboard_theme.yaml# Theme CSS variables and colors
├── deploy/                    # Deployment tools
│   ├── deploy_dashboard.py     # Deployment script for pushing changes to HA
│   ├── DEPLOYMENT.md          # Complete deployment guide with troubleshooting
│   └── requirements.txt      # Python dependencies for deployment
├── config/                    # Home Assistant configuration snippets
│   └── aqi_template_sensor.yaml # AQI sensor template configuration
├── opt/                       # Infrastructure configuration
│   └── docker-compose.yaml    # Docker compose configuration
├── README.md                  # This file
├── .clinerules               # Coding conventions and best practices
└── .gitignore                # Git ignore rules
```

### Key Files

| File | Purpose |
|------|---------|
| `my-dashboard.yaml` | Active working dashboard (edit this file) |
| `themes/my_dashboard_theme.yaml` | Dashboard theme with CSS variables and colors |
| `themes/bg.png` | Background image for dashboard |
| `deploy/deploy_dashboard.py` | Deployment script for pushing changes to HA |
| `deploy/DEPLOYMENT.md` | Complete deployment guide with troubleshooting |
| `config/aqi_template_sensor.yaml` | AQI sensor template configuration |
| `opt/docker-compose.yaml` | Docker compose configuration |
| `deploy/requirements.txt` | Python dependencies for deployment |

## 🏷️ Tagging / Checkpoints

| Tag | Points To | Description |
|-----|-----------|-------------|
| `dashboard-v1` | First commit | Original dashboard |
| `dashboard-v2` | Current | New dashboard with inline styles, teal backgrounds, section headers |
| `live-v1` | Same as v2 | First live deployment |

**Usage:**
- Compare versions: `git diff dashboard-v1 dashboard-v2 -- my-dashboard.yaml`
- View a past version: `git show dashboard-v2:my-dashboard.yaml`
- Tag a new checkpoint: `git tag -a dashboard-v3 -m "description"`
- Tag a live deploy: `git tag -a live-v2 -m "description"`

## 🔧 Development Workflow

1. Edit `my-dashboard.yaml` locally
2. Validate YAML syntax
3. Deploy with `python deploy/deploy_dashboard.py` (see [deploy/DEPLOYMENT.md](deploy/DEPLOYMENT.md) for details)
4. Verify in Home Assistant UI
5. Tag checkpoint: `git tag -a dashboard-vN -m "description"`
6. If deploying live: `git tag -a live-vN -m "description"`
7. Push all tags to remote: `git push origin --tags`

## 🚀 Quick Deploy

```bash
# Deploy to Home Assistant
python deploy/deploy_dashboard.py --host YOUR_HA_IP --user root --key ~/.ssh/id_rsa
```

> **Need detailed setup instructions?** See [deploy/DEPLOYMENT.md](deploy/DEPLOYMENT.md) for venv setup, SSH configuration, and troubleshooting.

## 📚 Documentation

- **[deploy/DEPLOYMENT.md](deploy/DEPLOYMENT.md)** - Complete deployment guide with troubleshooting
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

YAML anchors are defined once at the top level in the `_styles:` section and reused throughout:

| Anchor | Color | Usage |
|--------|-------|--------|
| `*style_section_header` | `var(--section-header-bg)` | Section headings |
| `*style_section_header_hidden` | `var(--section-header-bg)` + `display: none` | Hidden section headers |
| `*style_card` | `var(--card-bg)` | General cards using theme color |
| `*style_card_hidden` | `var(--card-bg)` + `display: none` | Hidden cards |
| `*style_greeting` | `var(--greeting-bg)` | Greeting banner |
| `*style_alert_red` | `var(--alert-red-bg)` | Weather alert cards |
| `*style_bubble_media` | Media player card styles | Bubble media player cards |
| `*style_chips_clean` | Clean chips styling | Mushroom chips cards |
| `*style_popup_padding` | Popup card padding | Mod-card popup styling |

### Theme CSS Variables

The dashboard uses a custom theme defined in `themes/my_dashboard_theme.yaml` with the following key variables:

**Dashboard Colors:**
- `--card-bg`: `rgba(30, 15, 60, 0.75)` - Background for cards
- `--section-header-bg`: `rgba(45, 25, 120, 0.85)` - Section header backgrounds
- `--greeting-bg`: `rgba(60, 35, 150, 0.85)` - Greeting banner
- `--alert-red-bg`: `rgb(220, 53, 69)` - Alert cards

**Bubble Card Defaults:**
- `--bubble-button-bg`: `rgba(30, 15, 60, 0.75)` - Button backgrounds
- `--bubble-icon-container-bg`: `#0F2C64` - Icon containers
- `--bubble-sub-button-on-color`: `#FF8000` - On state (orange)
- `--bubble-sub-button-off-color`: `#37474F` - Off state (dark grey)
- `--bubble-sub-button-text-color`: `white` - Sub-button text color
- `--bubble-sub-button-font-size`: `10px` - Sub-button font size

## 📖 More Information

- Home Assistant: https://www.home-assistant.io/
- Lovelace Documentation: https://www.home-assistant.io/lovelace/
- Deployment Guide: [deploy/DEPLOYMENT.md](deploy/DEPLOYMENT.md)