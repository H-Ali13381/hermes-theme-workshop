# Wofi Theming

Wofi (Wayland dmenu replacement) reads a CSS stylesheet from `~/.config/wofi/style.css`. The ricer **fully rewrites** this file from template — wofi has no include mechanism.

---

## How ricer.py Applies the Theme

1. Writes `~/.config/wofi/style.css` from `templates/wofi/style.css.template`
2. No reload needed — wofi reads its stylesheet fresh on each invocation

**Template variables used:**

| Variable | Role |
|----------|------|
| `{{name}}` | Theme name — written as a CSS comment header |
| `{{background}}` | Window + list background |
| `{{foreground}}` | Text color |
| `{{primary}}` | Window border, selected item highlight |
| `{{surface}}` | Input field background, entry hover |
| `{{muted}}` | Placeholder text |
| `{{accent}}` | Selected entry text |
| `{{danger}}` | (Not in default template — available for custom use) |
| `{{radius}}` | Border radius (from design_system `border_radius`, default `6px`) |

---

## CSS Selector Reference

| Selector | Element |
|----------|---------|
| `window` | The launcher window |
| `#input` | Search bar |
| `#outer-box` | Outer container |
| `#inner-box` | List container |
| `#entry` | Individual list item |
| `#entry:selected` | Currently highlighted item |
| `#text` | Text inside an entry |
| `#text:selected` | Text of selected entry |

---

## Example Styled Config

```css
window {
    background-color: #1a1a2e;
    border: 2px solid #7b5ea7;
    border-radius: 8px;
}

#entry:selected {
    background-color: #7b5ea7;
    border-radius: 4px;
}
```

---

## Wofi Config (`~/.config/wofi/config`)

Wofi's non-CSS config sets behavior, not colors. Useful options:

```ini
width=600
height=400
prompt=
hide_scroll=true
show=drun
term=kitty
```

The ricer does not modify the `config` file — only `style.css`.

---

## Pitfalls

- **Wofi doesn't reload on the fly.** Close any open wofi instance before applying — it reads CSS at launch only.
- **GTK theme bleeding.** If `gtk-theme` is set globally and wofi picks it up, some colors may be overridden by GTK. Force wofi to ignore GTK: `GTK_THEME=Adwaita:dark wofi` or set `style=` in the wofi config to point at the CSS file explicitly.
- **`border-radius` on `#entry` requires GTK 3.** On some builds, rounded entries don't render — fall back to `0` if corners look broken.
