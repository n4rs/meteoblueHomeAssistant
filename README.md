# Meteoblue Home Assistant Integration (HACS)

Custom integration for Home Assistant to fetch Meteoblue Weather API forecast packages.

## Supported packages (initial)
- Basic
- Current Conditions
- Clouds
- PV PRO

## Installation (HACS)
1. Add this repository as a custom repository in HACS (Integration category).
2. Install **Meteoblue**.
3. Restart Home Assistant.
4. Add integration from **Settings → Devices & Services**.

## Configuration
- API key (required)
- Location from Home Assistant core config (default) or manual coordinates
- Packages to fetch
- Update strategy:
  - Hourly interval (every N hours)
  - Daily at a specific hour

## Notes
- API payload structure may differ by package/contract; raw package payload is exposed as attributes in sensors.
- For PV PRO, additional parameters can be provided in options as JSON-like key/value settings in future revisions.
