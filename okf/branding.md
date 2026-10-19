# Branding

Matches mcalignerdev.com. All tokens in `app/ui/theme.py`.

| Token | Hex | Use |
|---|---|---|
| BG | #0B0F19 | app background (site bg, MJC mark backdrop) |
| SIDEBAR | #070B14 | sidebar (site theme-color) |
| SURFACE / SURFACE_2 | #121826 / #182033 | cards, rows, inputs |
| GOLD | #D39A1A | primary actions, active nav bar, results |
| BLUE | #6E8CFF | links, "working" state |
| SUCCESS / WARNING / DANGER | #3FB984 / #E8A33D / #F0616D | status |

- Type: Segoe UI (Windows), Cascadia Mono for sizes and numbers.
- Gold is for the one main action on screen and for results. Don't use it for secondary buttons.
- Logo: `assets/logo.png` if present, else a gold "MJC" monogram. App icon: gold rounded square, navy document, squeeze arrows (`scripts/make_icon.py`).
- Copy tone: short, plain, tells the user what happens next. No exclamation marks.
