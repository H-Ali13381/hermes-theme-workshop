# The Complete Guide to Ricing Linux on KDE Plasma
### From a Bare Install to a Jaw-Dropping Desktop — A to Z

---

## Table of Contents

1. [What Is Ricing?](#1-what-is-ricing)
2. [Prerequisites & Mindset](#2-prerequisites--mindset)
3. [Choosing Your Base Distro](#3-choosing-your-base-distro)
4. [KDE Plasma Basics & Installation](#4-kde-plasma-basics--installation)
5. [System Settings — The Foundation](#5-system-settings--the-foundation)
6. [Global Themes, Color Schemes & Plasma Styles](#6-global-themes-color-schemes--plasma-styles)
7. [Icons & Cursors](#7-icons--cursors)
8. [Fonts](#8-fonts)
9. [Window Decorations (KWin)](#9-window-decorations-kwin)
10. [Plasma Widgets & Panel Design](#10-plasma-widgets--panel-design)
11. [Kvantum — Deep Application Theming](#11-kvantum--deep-application-theming)
12. [GTK App Theming](#12-gtk-app-theming)
13. [Compositor & Desktop Effects (KWin Effects)](#13-compositor--desktop-effects-kwin-effects)
14. [Wallpapers](#14-wallpapers)
15. [Terminal Setup (Konsole / Kitty / Alacritty)](#15-terminal-setup-konsole--kitty--alacritty)
16. [Shell Customization (Bash / Zsh / Fish)](#16-shell-customization-bash--zsh--fish)
17. [Prompt Customization (Starship / Oh My Zsh / Oh My Posh)](#17-prompt-customization-starship--oh-my-zsh--oh-my-posh)
18. [Fetch Tools (Neofetch / Fastfetch)](#18-fetch-tools-neofetch--fastfetch)
19. [Application Launchers (KRunner, Rofi, Krunner Plugins)](#19-application-launchers-krunner-rofi-krunner-plugins)
20. [File Manager (Dolphin) Customization](#20-file-manager-dolphin-customization)
21. [Text Editor & IDE Theming](#21-text-editor--ide-theming)
22. [Tiling & Window Management](#22-tiling--window-management)
23. [Conky & Desktop Widgets](#23-conky--desktop-widgets)
24. [Latte Dock (Deprecated) vs. Native Panel Alternatives](#24-latte-dock-deprecated-vs-native-panel-alternatives)
25. [Login Screen (SDDM) Theming](#25-login-screen-sddm-theming)
26. [Plymouth — Boot Splash Screen](#26-plymouth--boot-splash-screen)
27. [GRUB Theming](#27-grub-theming)
28. [Audio Visualizers & Eye Candy](#28-audio-visualizers--eye-candy)
29. [Color Temperature & Night Mode](#29-color-temperature--night-mode)
30. [Dotfile Management & Backup](#30-dotfile-management--backup)
31. [Sharing Your Rice](#31-sharing-your-rice)
32. [Troubleshooting Common Ricing Problems](#32-troubleshooting-common-ricing-problems)
33. [Inspiration & Resources](#33-inspiration--resources)

---

## 1. What Is Ricing?

"Ricing" is the practice of customizing and beautifying a Linux desktop environment to a high degree. The term comes from car culture — "ricing out" a vehicle with custom modifications. In the Linux world, it means tweaking every visual and functional aspect of your desktop until it looks and feels exactly how you want.

A good rice isn't just pretty screenshots. It involves:

- **Visual cohesion** — colors, fonts, icons, and shapes that work together
- **Functional improvement** — your workflow should get *better*, not just prettier
- **Personality** — your desktop should look like *you* made it, not a template

KDE Plasma is arguably the most powerful desktop environment for ricing. Unlike GNOME (which requires extensions for basic customization) or lighter DEs (which require more manual effort), KDE provides deep, native theming infrastructure while also being compatible with almost every external tool.

---

## 2. Prerequisites & Mindset

Before touching a single setting, internalize these principles:

### Take Snapshots / Backups First
Always back up your current config before ricing. Use Timeshift or Snapper for full system snapshots, or at minimum back up `~/.config` and `~/.local/share`.

```bash
# Backup your KDE config manually
cp -r ~/.config/plasma* ~/backup/
cp -r ~/.local/share/plasma* ~/backup/
cp -r ~/.config/kdeglobals ~/backup/
```

### Know Your Aesthetic Goal
Before installing a single theme, decide on a direction:
- **Minimal/Clean** — flat icons, monochrome palette, no panel dock
- **macOS-inspired** — bottom or top bar, rounded windows, translucency
- **Cyberpunk/Neon** — dark base, vivid accent colors, glow effects
- **Gruvbox/Nord/Catppuccin** — warm or cool muted palettes, very popular on r/unixporn
- **Retro/CRT** — scanline effects, old-school terminal fonts, dark themes

### Learn the KDE Config Hierarchy
KDE stores its config in several key places:

| Path | Contents |
|------|----------|
| `~/.config/kdeglobals` | Global color scheme, fonts |
| `~/.config/plasma-org.kde.plasma.desktop-appletsrc` | Panel & widget layout |
| `~/.config/kwinrc` | Window manager settings |
| `~/.config/kscreenlockerrc` | Lock screen config |
| `~/.local/share/plasma/` | Installed themes |
| `~/.local/share/icons/` | User-installed icon sets |
| `~/.local/share/color-schemes/` | Color scheme files (.colors) |
| `/usr/share/plasma/` | System-wide themes |
| `/usr/share/icons/` | System-wide icons |

---

## 3. Choosing Your Base Distro

The distro matters less than you'd think for KDE ricing, but some choices make life easier:

### Recommended Distros for KDE Ricing

| Distro | Reason |
|--------|--------|
| **KDE Neon** | Always the latest KDE Plasma; Ubuntu base; great for trying new KDE features |
| **Arch Linux** | Maximum control; AUR has nearly every rice tool; rolling release |
| **EndeavourOS** | Arch-based, beginner-friendly, good KDE spin |
| **Garuda Linux** | Ships with a pre-riced KDE; great baseline to customize further |
| **openSUSE Tumbleweed** | Excellent KDE integration; rolling release; Zypper is solid |
| **Fedora KDE Spin** | Modern, stable, RPM-based; good Wayland support |
| **Manjaro KDE** | Arch-based, stable-ish, beginner-friendly |

### Wayland vs. X11
- **Wayland** is the future. Most ricing tools now support it. KDE's Wayland session is production-ready as of Plasma 6.
- **X11** has broader legacy tool support (e.g., some Conky features, xdotool, xrandr).
- For maximum ricing compatibility in 2024+, **Wayland** is recommended on modern hardware. Fall back to X11 only if a specific tool demands it.

---

## 4. KDE Plasma Basics & Installation

### Installing KDE Plasma

**Arch Linux:**
```bash
sudo pacman -S plasma kde-applications
# Or minimal install:
sudo pacman -S plasma-meta
```

**Fedora:**
```bash
sudo dnf groupinstall "KDE Plasma Workspaces"
```

**Ubuntu/Debian:**
```bash
sudo apt install kde-plasma-desktop
# Or full suite:
sudo apt install kde-full
```

### Essential KDE Components to Know

| Component | Role |
|-----------|------|
| **KWin** | Window manager + compositor |
| **Plasmashell** | Desktop shell (panel, widgets) |
| **KDE Systemsettings** | Central configuration GUI |
| **KSVG / Plasma Framework** | SVG-based theme engine for panels/widgets |
| **KDecoration2** | Window decoration (title bar) API |
| **Kvantum** | Qt5/Qt6 style engine (theme app interiors) |
| **SDDM** | Login display manager |

### Restarting Plasma Without Rebooting

```bash
# Restart Plasmashell (panel, widgets):
plasmashell --replace &

# Restart KWin (compositor, window manager):
kwin_wayland --replace &   # on Wayland
kwin_x11 --replace &       # on X11

# Or use kquitapp + restart:
kquitapp5 plasmashell && kstart5 plasmashell
```

---

## 5. System Settings — The Foundation

Open **System Settings** (`systemsettings` in terminal, or from app launcher). This is your ricing command center.

### Key Sections for Ricing

- **Appearance → Global Theme** — Apply a complete theme bundle
- **Appearance → Application Style** — Qt widget style (Breeze, Oxygen, Kvantum)
- **Appearance → Plasma Style** — Panel/widget visual style
- **Appearance → Colors** — Color scheme
- **Appearance → Window Decorations** — Title bar style
- **Appearance → Fonts** — System-wide fonts
- **Appearance → Icons** — Icon pack
- **Appearance → Cursors** — Cursor theme
- **Appearance → Splash Screen** — Boot-up splash
- **Workspace → Desktop Effects** — Visual effects, blur, transparency
- **Workspace → Screen Locking** — Lock screen appearance
- **Hardware → Display and Monitor** — DPI, scaling, refresh rate

### DPI & Scaling
For HiDPI displays, set your scale factor under **Display and Monitor → Scale**. KDE handles fractional scaling (e.g., 1.25×, 1.5×) well on Wayland. On X11, use:

```bash
# In ~/.Xresources
Xft.dpi: 144  # For 150% on a 96dpi-baseline display
```

Then apply with:
```bash
xrdb ~/.Xresources
```

---

## 6. Global Themes, Color Schemes & Plasma Styles

### Global Themes

A Global Theme bundles together: Plasma Style, Color Scheme, Window Decoration, Icons, Cursors, and Splash Screen.

**Installing from the KDE Store:**
System Settings → Global Theme → Get New Global Themes…

**Installing manually:**
```bash
# Place theme folder in:
~/.local/share/plasma/look-and-feel/
```

**Popular Global Themes:**

| Theme | Aesthetic |
|-------|-----------|
| Breeze | Default KDE; clean, flat |
| Breeze Dark | Dark Breeze; great base |
| Catppuccin | Pastel, soft, very popular |
| Nord KDE | Cool blue-grey palette |
| Gruvbox | Warm retro palette |
| Sweet | Colorful, vibrant, modern |
| Layan | macOS-inspired, glassmorphism |
| WhiteSur | macOS Big Sur look |
| Utterly Dark | Deep dark with subtle accents |
| Orchis | Material Design inspired |

### Color Schemes

Color schemes control the palette of all KDE/Qt apps. They are `.colors` files.

**Installing:**
```bash
# Drop .colors files into:
~/.local/share/color-schemes/

# Then select in System Settings → Colors
```

**Editing Color Schemes:**
System Settings → Colors → Edit Scheme — lets you customize every color role:
- Window background, text, button, selection highlight, link color, etc.

**Creating from scratch:**
Each `.colors` file is an INI file. Example snippet:

```ini
[Colors:Window]
BackgroundNormal=30,30,46
ForegroundNormal=205,214,244

[Colors:Button]
BackgroundNormal=49,50,68
ForegroundNormal=205,214,244

[General]
ColorScheme=MyCatppuccinMocha
Name=My Catppuccin Mocha
```

### Plasma Styles

Plasma Style controls the visual appearance of panels, widgets, tooltips, and the task switcher. These are SVG-based themes.

**Location:**
```bash
~/.local/share/plasma/desktoptheme/
```

**Popular Plasma Styles:**

| Style | Notes |
|-------|-------|
| Breeze Dark | Solid default dark |
| Blur Glass | Translucent/blurred panels |
| Layan | Elegant translucency |
| Moe | Rounded, colorful |
| Aritim-Dark | Very dark, minimal |
| ChromeOS | Mimics ChromeOS panels |

**Editing Plasma Styles:**
Each theme folder contains SVG files. You can edit colors in any SVG editor (Inkscape) or directly in a text editor. Key file: `colors` inside the theme folder defines the named colors used throughout.

---

## 7. Icons & Cursors

### Icon Themes

**Install location:**
```bash
~/.local/share/icons/
# or system-wide:
/usr/share/icons/
```

**From KDE Store:**
System Settings → Icons → Get New Icons…

**Manually:**
```bash
# Most icon packs come as .tar.gz:
tar -xf IconPack.tar.gz -C ~/.local/share/icons/
```

**Popular Icon Packs:**

| Icon Pack | Aesthetic |
|-----------|-----------|
| Papirus | Flat, colorful, massive library |
| Papirus-Dark | Dark variant |
| Tela | Flat, Google-inspired |
| Numix Circle | Circular icons |
| Fluent | Microsoft Fluent Design |
| BeautyLine | Outlined, elegant |
| Candy | Bright, macOS-like |
| Reversal | Colorful circles |
| Win11 | Windows 11 style |

**Papirus Folder Colors:**
Papirus supports custom folder colors via `papirus-folders`:

```bash
# Install (AUR on Arch):
yay -S papirus-folders

# Set folder color:
papirus-folders -C cat-mocha-lavender --theme Papirus-Dark
```

### Cursor Themes

**Install location:**
```bash
~/.local/share/icons/   # Yes, cursors go in the icons directory
# Each cursor theme has a 'cursors' subfolder
```

**Popular Cursor Themes:**

| Cursor | Style |
|--------|-------|
| Bibata Modern | Sharp, modern |
| Phinger | Cute, chubby |
| Capitaine | macOS-like |
| Volantes | Minimal, elegant |
| Breeze | KDE default |
| Oxygen | KDE classic |
| WhiteSur | macOS Big Sur |

**Forcing cursor theme system-wide:**
Create/edit `~/.icons/default/index.theme`:
```ini
[Icon Theme]
Name=Default
Comment=Default Cursor Theme
Inherits=Bibata-Modern-Classic
```

Also set in `~/.config/gtk-3.0/settings.ini` and `~/.Xresources` for full coverage:
```
Xcursor.theme: Bibata-Modern-Classic
Xcursor.size: 24
```

---

## 8. Fonts

Fonts make or break a rice. KDE lets you set different fonts for different UI elements.

### System Settings → Fonts

| Setting | Recommendation |
|---------|---------------|
| General | Inter, Noto Sans, Roboto, Source Sans 3 |
| Fixed Width | JetBrains Mono, Cascadia Code, Iosevka, Fira Code |
| Small | Same as General, -1pt |
| Toolbar | Same as General |
| Menu | Same as General |
| Window Title | Same as General, sometimes Bold |

### Installing Fonts

```bash
# User fonts:
mkdir -p ~/.local/share/fonts
cp MyFont.ttf ~/.local/share/fonts/
fc-cache -fv

# System fonts:
sudo cp MyFont.ttf /usr/share/fonts/
sudo fc-cache -fv
```

### Nerd Fonts (Essential for Terminal Ricing)
Nerd Fonts patch developer fonts with thousands of glyphs (icons) used by shell prompts, nvim plugins, etc.

```bash
# AUR:
yay -S ttf-jetbrains-mono-nerd
yay -S ttf-firacode-nerd
yay -S nerd-fonts-iosevka

# Manual: download from https://www.nerdfonts.com/
```

### Font Rendering
For crisp fonts, especially on LCD screens, tune antialiasing:

System Settings → Fonts → Anti-Aliasing → Configure…
- **Anti-aliasing**: Enabled
- **Sub-pixel rendering**: RGB (for most monitors)
- **Hinting**: Slight or Medium

Or edit `~/.config/fontconfig/fonts.conf`:
```xml
<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<fontconfig>
  <match target="font">
    <edit name="antialias" mode="assign"><bool>true</bool></edit>
    <edit name="hinting" mode="assign"><bool>true</bool></edit>
    <edit name="hintstyle" mode="assign"><const>hintslight</const></edit>
    <edit name="rgba" mode="assign"><const>rgb</const></edit>
    <edit name="lcdfilter" mode="assign"><const>lcddefault</const></edit>
  </match>
</fontconfig>
```

---

## 9. Window Decorations (KWin)

Window decorations are the title bars and borders around windows.

### Installing Decorations

System Settings → Window Decorations → Get New Window Decorations…

**Manual installation:**
```bash
# Decoration plugins are compiled C++ KDecoration2 plugins
# Most are installed via package manager or AUR:
yay -S kwin-decoration-sierra-breeze-enhanced
yay -S kwin-decoration-klassy
```

**Popular Window Decorations:**

| Decoration | Style |
|-----------|-------|
| Breeze | KDE default |
| **Klassy** | Highly configurable; rounded, minimal |
| Sierra Breeze Enhanced | macOS Big Sur style |
| Aurorae themes | SVG-based; many on KDE Store |
| Lightly | Clean, modern |
| Bismuth/Krohnkite | Tiling-focused |

### Aurorae Themes
Aurorae is KDE's SVG-based window decoration engine — no compilation needed.

```bash
# Install Aurorae theme:
mkdir -p ~/.local/share/aetheme/decorations/
# Or the proper path:
~/.local/share/aurorae/themes/
```

Then select it in System Settings → Window Decorations.

### Klassy — The Power User Choice
Klassy is arguably the most feature-rich decoration available:

```bash
yay -S klassy
```

Klassy lets you control:
- Corner radius (per-corner)
- Button size, spacing, and style
- Thin/thick borders
- Accent color from title bar
- Integration with KDE color schemes
- Shadow customization

### Custom Title Bar Buttons

System Settings → Window Decorations → (your theme) → Configure Buttons

Drag to reorder: Close, Minimize, Maximize, On-All-Desktops, Keep-Above, Menu, etc.

For macOS-style left-side buttons, drag them to the left side of the title bar.

---

## 10. Plasma Widgets & Panel Design

### Panel Setup

Right-click the desktop → Add Panel, or right-click existing panel → Enter Edit Mode.

**Panel positions:** Top, Bottom, Left, Right — you can have multiple panels.

**Panel properties (Edit Mode):**
- Width / Height
- Floating (adds gap from screen edge — very popular in modern rices)
- Opacity (requires blur effect)
- Auto-hide / Dodge windows

### Essential Widgets

| Widget | Use |
|--------|-----|
| Application Launcher (Kickoff) | App menu |
| Application Menu (Global Menu) | macOS-style menu bar |
| Task Manager | Window taskbar |
| Icons-Only Task Manager | Dock-style taskbar |
| System Tray | Notification area |
| Digital Clock | Clock |
| Pager | Virtual desktop switcher |
| Window Title | Shows active window title |
| Window Buttons | Shows window controls on panel |
| Spacer | Flexible/fixed spacing |
| Event Calendar | Clock + calendar widget |
| Panel Colorizer | Per-panel color/transparency control |

### Get New Widgets

```bash
# From KDE Store:
System Settings → (right-click panel in edit mode) → Add Widgets → Get New Widgets

# Or via Plasma package:
plasma-apply-widgetstyle  # rarely used directly
```

**Popular third-party widgets:**

| Widget | Function |
|--------|----------|
| **Panel Colorizer** | Per-panel gradient, transparency, blur |
| **Plasma Drawer** | Full-screen app grid launcher |
| Event Calendar | Rich clock + calendar |
| Thermal Monitor | CPU/GPU temps |
| Resources Monitor Fork | CPU/RAM usage graphs |
| Latte Separator | Visual divider |
| Window Title Applet | Active window name in panel |

### A Clean Minimal Panel Setup

Example for a floating top bar:

```
[Application Menu] [Spacer-flexible] [Window Title] [Spacer-flexible] [Clock] [System Tray]
```

Panel settings: Floating ✓, Height: 36px, Opacity: 70%, Blur: enabled (via KWin effects)

### A macOS-Style Setup

- Top panel: Global Menu + Spacer + Clock + System Tray
- Bottom floating panel: Icons-Only Task Manager (centered, fixed width)
- Window buttons in panel (not title bar)
- Title bar buttons: left-side close/min/max

---

## 11. Kvantum — Deep Application Theming

Kvantum is a Qt style engine that themes the **interior** of Qt apps (buttons, menus, scrollbars, checkboxes, etc.) using SVG-based themes. It goes far deeper than what KDE's built-in Breeze style offers.

### Installation

```bash
# Arch:
sudo pacman -S kvantum

# Fedora:
sudo dnf install kvantum

# Ubuntu:
sudo apt install qt5-style-kvantum
```

### Using Kvantum

1. Open `kvantummanager` (Kvantum Manager)
2. Install a theme: "Install a theme" tab → select `.tar.gz` theme
3. Select it: "Change/Delete Theme" tab → select → "Use this theme"
4. In KDE System Settings → Application Style → set to **kvantum** or **kvantum-dark**

### Popular Kvantum Themes

| Theme | Style |
|-------|-------|
| Catppuccin-Mocha | Pastel dark |
| KvLibadwaita | Matches GNOME's Adwaita |
| Layan | Glassmorphism |
| Nordic | Nord-inspired |
| Orchis | Material Design |
| Sweet | Colorful, vibrant |
| Fluent-Dark | Windows 11 inspired |

### Tuning Kvantum
Kvantum Manager's "Configure Active Theme" tab lets you adjust:
- Window transparency
- Blur
- Reduce window opacity when inactive
- Scrollbar width
- Menu opacity

---

## 12. GTK App Theming

KDE is Qt-based, but many apps you'll use (Firefox, Nautilus, GIMP, etc.) are GTK apps. Theming them requires separate setup.

### GTK3 Theming

```bash
# Config file:
~/.config/gtk-3.0/settings.ini
```

```ini
[Settings]
gtk-theme-name=Catppuccin-Mocha-Standard-Lavender-Dark
gtk-icon-theme-name=Papirus-Dark
gtk-cursor-theme-name=Bibata-Modern-Classic
gtk-cursor-theme-size=24
gtk-font-name=Inter 11
gtk-application-prefer-dark-theme=1
```

### GTK4 Theming

GTK4 uses a different theming system (libadwaita). Theming it requires either:

```bash
# Option 1: Use adw-gtk3 for GTK3/4 consistency:
yay -S adw-gtk3

# Option 2: Force libadwaita color override:
mkdir -p ~/.config/gtk-4.0
# Create ~/.config/gtk-4.0/gtk.css with color overrides
```

Catppuccin provides ready-made GTK4 configs:
```bash
# Copy the provided gtk.css to ~/.config/gtk-4.0/gtk.css
```

### KDE's GTK Theme Sync

KDE can apply GTK themes automatically:

System Settings → Appearance → Application Style → Configure GNOME/GTK Application Style

Or install `kde-gtk-config` and use the GUI to set GTK2/3 themes.

### Flatpak App Theming

Flatpak apps are sandboxed — they don't see your system themes by default.

```bash
# Allow Flatpak apps to see GTK themes:
sudo flatpak override --filesystem=$HOME/.themes
sudo flatpak override --filesystem=$HOME/.icons
sudo flatpak override --env=GTK_THEME=Catppuccin-Mocha-Standard-Lavender-Dark

# Or per-app:
flatpak override --user --env=GTK_THEME=YourTheme org.mozilla.firefox
```

For Qt Flatpak apps, you may need:
```bash
sudo flatpak override --env=QT_STYLE_OVERRIDE=kvantum
```

---

## 13. Compositor & Desktop Effects (KWin Effects)

KWin is KDE's window manager and compositor. Its effects system is where the visual magic happens.

### Enabling/Disabling Compositor

System Settings → Display and Monitor → Compositor

- **Rendering backend:** OpenGL 3.1 (recommended), OpenGL 2.0, or XRender
- **Tearing prevention (VSync):** Automatic or Full Screen Repaints
- **Scale method:** Crisp (pixel art), Smooth (general), or Accurate

```bash
# Toggle compositor (X11 only):
qdbus org.kde.KWin /Compositor toggleCompositing
```

### KWin Desktop Effects

System Settings → Workspace → Desktop Effects

**Must-have effects for ricing:**

| Effect | Purpose |
|--------|---------|
| **Background Contrast** | Darkens areas behind translucent elements |
| **Blur** | Blurs what's behind panels/windows |
| **Wobbly Windows** | Classic jellyfied window animation |
| **Magic Lamp** | macOS-style minimize animation |
| **Overview** | GNOME Activities-style window overview |
| **Desktops Grid** | Virtual desktop thumbnail grid |
| **Scale** | Window open/close scale animation |
| **Slide** | Slide when switching virtual desktops |
| **Translucency** | Make inactive windows transparent |
| **Sheet** | macOS sheet drop animation |
| **Fall Apart** | Windows explode into particles on close |
| **Glide** | Glide + fade window animations |

### Blur Effect Configuration

The Blur effect is central to most modern KDE rices (glassmorphism look).

System Settings → Desktop Effects → Blur → Configure:
- **Blur Strength:** 10–15 for subtle, 20+ for heavy
- **Noise Strength:** Adds grain texture (optional)

For this to be visible, your panels and windows must have transparency enabled (via Kvantum, Plasma Style, or KWin rules).

### KWin Rules — Per-Window Settings

KWin Rules let you apply specific settings to specific windows (transparency, borders, geometry, etc.).

System Settings → Window Management → Window Rules → Add New…

Example: Make a terminal window 80% opaque:
- Match: `Window class contains 'konsole'`
- Apply: `Opacity Active = 80`

Or via right-click title bar → More Options → Special Window Settings.

### Animation Speed

System Settings → Workspace → General Behavior → Animation Speed

Drag toward "Instant" for a snappier feel, toward "Very Slow" for dramatic effects.

---

## 14. Wallpapers

The wallpaper is your canvas. Everything else should complement it.

### Setting a Wallpaper

Right-click Desktop → Configure Desktop and Wallpaper → Wallpaper Type:

| Type | Use Case |
|------|----------|
| Image | Static image |
| Slideshow | Rotating images |
| Color | Solid color (minimalist) |
| Dynamic Wallpaper (Plasma 6) | Time-of-day changing |
| Video (KDE plugin) | Video loop |
| Havoc (plugin) | Particles simulation |

### Finding Wallpapers

- **r/wallpaper**, **r/wallpapers** — vast community
- **Unsplash** (unsplash.com) — high quality free photos
- **WallHaven** (wallhaven.cc) — massive curated collection, filter by color
- **KDE Store** — wallpaper packs, dynamic wallpapers
- **Bing Wallpaper** — daily wallpapers via plugin

### Color-Matching Your Wallpaper

The key to a cohesive rice is deriving your color scheme from the wallpaper. Tools:

```bash
# pywal — generates color schemes from wallpaper:
pip install pywal
wal -i /path/to/wallpaper.jpg

# Pywalfox — applies wal colors to Firefox:
pip install pywalfox
pywalfox install

# wpgtk — GUI for pywal:
pip install wpgtk
```

`pywal` generates colors in `~/.cache/wal/colors.json` and applies them to terminals, some apps, and can generate theme files.

For KDE integration:
```bash
# Apply wal colors to KDE:
pip install pywal
yay -S wal-kde  # or kde-pywal from AUR
```

---

## 15. Terminal Setup (Konsole / Kitty / Alacritty)

The terminal is the heart of any rice. Spend time here.

### Konsole (Default KDE Terminal)

**Profile settings:** Settings → Manage Profiles → Edit

- **Font:** JetBrainsMono Nerd Font, size 12
- **Color scheme:** Custom or installed from KDE Store
- **Opacity:** 85–95% (requires compositor)
- **Blur background:** Check if Blur effect is enabled
- **Cursor shape:** Block / Underline / I-Beam

**Installing Konsole color schemes:**
```bash
# Drop .colorscheme files into:
~/.local/share/konsole/
```

**Popular Konsole color schemes:**
- Catppuccin-Mocha, Nord, Gruvbox, Tokyo Night, One Dark, Dracula

### Kitty — GPU-Accelerated Terminal

```bash
sudo pacman -S kitty  # Arch
sudo apt install kitty  # Ubuntu
```

Config: `~/.config/kitty/kitty.conf`

```conf
# Font
font_family      JetBrainsMono Nerd Font
font_size        13.0

# Opacity
background_opacity 0.90
blur_radius 10  # Requires KWin blur + compositor support

# Catppuccin Mocha colors
background            #1E1E2E
foreground            #CDD6F4
selection_background  #F5E0DC
selection_foreground  #1E1E2E
cursor                #F5E0DC

color0  #45475A
color1  #F38BA8
color2  #A6E3A1
color3  #F9E2AF
color4  #89B4FA
color5  #F5C2E7
color6  #94E2D5
color7  #BAC2DE

# Window
hide_window_decorations yes
window_padding_width 12

# Tabs
tab_bar_style powerline
tab_powerline_style round
```

### Alacritty — Minimal GPU Terminal

Config: `~/.config/alacritty/alacritty.toml` (TOML format since v0.13)

```toml
[window]
opacity = 0.9
padding.x = 12
padding.y = 12
decorations = "None"

[font]
normal.family = "JetBrainsMono Nerd Font"
size = 13.0

[colors.primary]
background = "#1E1E2E"
foreground = "#CDD6F4"

[colors.normal]
black =   "#45475A"
red =     "#F38BA8"
green =   "#A6E3A1"
yellow =  "#F9E2AF"
blue =    "#89B4FA"
magenta = "#F5C2E7"
cyan =    "#94E2D5"
white =   "#BAC2DE"
```

### Foot — Wayland-Native Terminal

A great lightweight choice for pure Wayland setups:
```bash
sudo pacman -S foot
```
Config: `~/.config/foot/foot.ini`

---

## 16. Shell Customization (Bash / Zsh / Fish)

### Choosing a Shell

| Shell | Pros | Cons |
|-------|------|------|
| **Bash** | Universal, always available | Minimal features out of box |
| **Zsh** | Powerful, huge plugin ecosystem (Oh My Zsh) | Needs setup |
| **Fish** | Beautiful defaults, auto-suggestions built-in | Non-POSIX syntax |
| **Nushell** | Structured data, modern | Very different paradigm |

### Switching Shells

```bash
# Install zsh:
sudo pacman -S zsh

# Set as default:
chsh -s $(which zsh)

# Install fish:
sudo pacman -S fish
chsh -s $(which fish)
```

### Essential Shell Quality-of-Life

```bash
# ~/.zshrc or ~/.bashrc additions:

# Better history
HISTSIZE=10000
HISTFILE=~/.zsh_history
setopt HIST_IGNORE_DUPS
setopt SHARE_HISTORY

# Aliases
alias ls='eza --icons'        # eza: modern ls replacement
alias ll='eza -la --icons'
alias cat='bat'               # bat: modern cat with syntax highlighting
alias grep='rg'               # ripgrep: modern grep
alias find='fd'               # fd: modern find
alias cd='z'                  # zoxide: smart directory jumper
alias top='btop'              # btop: beautiful system monitor
alias vim='nvim'              # neovim
```

### Modern CLI Tool Replacements

Install these — they're faster, prettier, and more useful:

```bash
# Arch:
sudo pacman -S eza bat ripgrep fd zoxide btop

# They replace: ls, cat, grep, find, cd tracking, top
```

---

## 17. Prompt Customization (Starship / Oh My Zsh / Oh My Posh)

### Starship — Universal, Fast, Beautiful

Starship works in any shell. It's written in Rust and extremely fast.

```bash
# Install:
curl -sS https://starship.rs/install.sh | sh
# or:
sudo pacman -S starship

# Add to ~/.zshrc:
eval "$(starship init zsh)"
# or ~/.bashrc:
eval "$(starship init bash)"
# or ~/.config/fish/config.fish:
starship init fish | source
```

**Config:** `~/.config/starship.toml`

```toml
format = """
[╭─](bold green)$os$username$hostname$directory$git_branch$git_status
[╰─](bold green)$character"""

[character]
success_symbol = "[❯](bold green)"
error_symbol = "[❯](bold red)"

[directory]
style = "bold cyan"
truncate_to_repo = false
truncation_length = 3

[git_branch]
symbol = " "
style = "bold purple"

[git_status]
style = "bold red"

[os]
disabled = false
style = "bold blue"
```

### Oh My Zsh — The Plugin Framework

```bash
# Install:
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
```

**Essential plugins** (set in `~/.zshrc`):
```bash
plugins=(
  git
  zsh-autosuggestions
  zsh-syntax-highlighting
  z
  sudo
  colored-man-pages
  copypath
  dirhistory
)
```

**Install third-party plugins:**
```bash
# zsh-autosuggestions:
git clone https://github.com/zsh-users/zsh-autosuggestions ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-autosuggestions

# zsh-syntax-highlighting:
git clone https://github.com/zsh-users/zsh-syntax-highlighting ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting
```

**Themes with Oh My Zsh:**
Use any theme from `~/.oh-my-zsh/themes/`, or set `ZSH_THEME="powerlevel10k/powerlevel10k"` for p10k:

```bash
git clone --depth=1 https://github.com/romkatv/powerlevel10k.git ${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/themes/powerlevel10k
# Then: ZSH_THEME="powerlevel10k/powerlevel10k" in .zshrc
# Run: p10k configure
```

### Fish with Fisher (Plugin Manager)

```bash
# Install Fisher:
curl -sL https://raw.githubusercontent.com/jorgebucaran/fisher/main/functions/fisher.fish | source && fisher install jorgebucaran/fisher

# Install tide prompt (like p10k for fish):
fisher install IlanCosman/tide@v6

# Install useful plugins:
fisher install PatrickF1/fzf.fish
fisher install jorgebucaran/autopair.fish
fisher install jhillyerd/plugin-git
```

---

## 18. Fetch Tools (Neofetch / Fastfetch)

A fetch tool displays system info with ASCII/image art. It's the signature of any rice screenshot.

### Fastfetch (Recommended — Neofetch Successor)

Neofetch is unmaintained. Use Fastfetch:

```bash
sudo pacman -S fastfetch
```

**Config:** `~/.config/fastfetch/config.jsonc`

```jsonc
{
  "$schema": "https://github.com/fastfetch-cli/fastfetch/raw/dev/doc/json_schema.json",
  "logo": {
    "type": "kitty",
    "source": "/path/to/your/image.png",
    "width": 30,
    "height": 15
  },
  "display": {
    "separator": " → ",
    "color": {
      "keys": "blue",
      "title": "cyan"
    }
  },
  "modules": [
    "title",
    "separator",
    "os",
    "kernel",
    "packages",
    "shell",
    {"type": "de", "format": "{2} {3}"},
    "wm",
    "terminal",
    "cpu",
    "gpu",
    "memory",
    "disk",
    "uptime",
    "colors"
  ]
}
```

### Displaying Images in Terminal

For image support in fetch tools, use:
- **Kitty terminal** + kitty image protocol (`--logo-type kitty`)
- **Sixel** capable terminals (mlterm, foot, xterm with sixel)
- **Ueberzug++** for X11 image display in terminals

```bash
# In kitty:
fastfetch --logo-type kitty --logo /path/to/art.png
```

### ASCII Art Logos

Custom ASCII art goes in the fastfetch config or you can use `--logo` flag:
```bash
fastfetch --logo Arch  # Built-in logos
fastfetch --logo-color-1 blue --logo-color-2 cyan
```

---

## 19. Application Launchers (KRunner, Rofi, KRunner Plugins)

### KRunner — KDE's Built-in Launcher

Activate with `Alt+Space` or `Alt+F2`.

**KRunner Plugins** (extend what KRunner can do):
- Calculator
- Unit converter
- Browser history
- Spell checker
- Dictionary
- Window switcher
- Session management

### Rofi — The Power User Launcher

Rofi is a generic menu/launcher that's highly customizable.

```bash
sudo pacman -S rofi
# Or rofi-wayland for Wayland:
yay -S rofi-wayland
```

**Basic usage:**
```bash
rofi -show drun         # App launcher
rofi -show window       # Window switcher
rofi -show run          # Command runner
```

**Config:** `~/.config/rofi/config.rasi`

```rasi
configuration {
  modi: "drun,window,run";
  font: "JetBrainsMono Nerd Font 12";
  show-icons: true;
  icon-theme: "Papirus-Dark";
  drun-display-format: "{name}";
  display-drun: " Apps";
  display-window: " Windows";
}

@theme "catppuccin-mocha"
```

**Rofi Themes:**
```bash
# Clone catppuccin rofi:
git clone https://github.com/catppuccin/rofi ~/.config/rofi/themes/catppuccin

# Or install rofi-themes-collection:
yay -S rofi-themes-collection-git
```

**Bind Rofi to a Keyboard Shortcut:**
System Settings → Shortcuts → Custom Shortcuts → Add Command
- Trigger: keyboard shortcut (e.g., `Super+D`)
- Command: `rofi -show drun`

### Wofi — Wayland-native Rofi Alternative

```bash
sudo pacman -S wofi
# Config: ~/.config/wofi/config
# Style: ~/.config/wofi/style.css
```

---

## 20. File Manager (Dolphin) Customization

Dolphin is KDE's file manager. It's incredibly powerful and themeable.

### Visual Settings

View → Adjust View Properties:
- **Icon size**
- **Grid/List/Compact** view
- **Show hidden files** (Ctrl+H)

### Dolphin Configuration

Settings → Configure Dolphin:
- **Startup:** Show Places panel, set default folder
- **View Modes:** Thumbnail size, icon size
- **Navigation:** Single/double click, breadcrumbs style
- **Services:** Right-click actions

### Custom Toolbar

Right-click toolbar → Configure Toolbars → drag items in/out

### Useful Dolphin Plugins

```bash
# Dolphin plugins (AUR):
yay -S dolphin-plugins  # git integration, compressed files, etc.
yay -S kde-servicemenus-rootactions  # open as root
```

### Terminal Integration

Dolphin has a built-in terminal panel: F4 to toggle.
It respects your default shell and theme.

---

## 21. Text Editor & IDE Theming

### Kate / KWrite

Kate is KDE's powerful text editor. It follows KDE color schemes natively.

Settings → Color Themes → pick or customize.

### Neovim — The Rice Showpiece

Neovim is the favorite text editor among ricers. Its appearance in screenshots is often what makes a rice stand out.

```bash
sudo pacman -S neovim
```

**Config:** `~/.config/nvim/` (Lua-based since Neovim 0.5+)

**Plugin manager — lazy.nvim:**
```lua
-- ~/.config/nvim/init.lua
local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
if not vim.loop.fs_stat(lazypath) then
  vim.fn.system({"git", "clone", "--filter=blob:none",
    "https://github.com/folke/lazy.nvim.git", "--branch=stable", lazypath})
end
vim.opt.rtp:prepend(lazypath)

require("lazy").setup({
  -- Catppuccin theme:
  { "catppuccin/nvim", name = "catppuccin", priority = 1000 },
  -- Status line:
  { "nvim-lualine/lualine.nvim" },
  -- File tree:
  { "nvim-tree/nvim-tree.lua" },
  -- Icons:
  { "nvim-tree/nvim-web-devicons" },
  -- Syntax:
  { "nvim-treesitter/nvim-treesitter" },
  -- Dashboard:
  { "goolord/alpha-nvim" },
  -- Bufferline (tabs):
  { "akinsho/bufferline.nvim" },
})

vim.cmd.colorscheme("catppuccin-mocha")
```

### VS Code Theming

VS Code follows system GTK theming for its chrome, but its editor theme is set internally.

Settings → Color Theme → install from Extensions marketplace:
- One Dark Pro, Catppuccin, Tokyo Night, Gruvbox, Dracula

For full transparency:
```bash
yay -S vscode-vibrancy  # Electron transparency hack
```

---

## 22. Tiling & Window Management

### KWin Tiling (Plasma 5.27+)

KDE Plasma 5.27 introduced built-in tiling. Enable it:
System Settings → Window Management → KWin Tiling → Enable Tiling

Or via Quick Tile shortcuts: `Super+Left/Right/Up/Down`

Configure tiling layouts per virtual desktop. It's relatively basic compared to dedicated tiling WMs.

### KWin Scripts for Advanced Tiling

```bash
# Install tiling scripts from KDE Store or AUR:
yay -S kwin-script-krohnkite  # i3-like tiling
yay -S kwin-script-polonium   # Plasma 6 tiling script
yay -S kwin-script-bismuth    # (Plasma 5, discontinued in 6)
```

**Polonium** (Plasma 6) is the current recommended tiling script:
```bash
yay -S kwin-script-polonium
```

It supports: Spiral, Binary Space Partition, Three-Column, Monocle layouts.

### Window Gaps

Via KWin Scripts or KWin Rules, you can add gaps around windows — common in rice screenshots.

With Polonium:
```
Settings → KWin Scripts → Polonium → Configure
Gap size: 8px
```

### Virtual Desktops

System Settings → Window Management → Virtual Desktops

- Create multiple desktops
- Name them (browser, dev, media, etc.)
- Enable "Different widgets per desktop" for per-desktop wallpapers
- Assign keyboard shortcuts

---

## 23. Conky & Desktop Widgets

### Conky

Conky is a lightweight system monitor that renders directly on the desktop.

```bash
sudo pacman -S conky
```

**Config:** `~/.config/conky/conky.conf`

```lua
conky.config = {
    alignment = 'top_right',
    background = false,
    border_width = 0,
    cpu_avg_samples = 2,
    default_color = 'CCEEFF',
    double_buffer = true,
    draw_shades = false,
    font = 'JetBrainsMono Nerd Font:size=10',
    gap_x = 30,
    gap_y = 60,
    own_window = true,
    own_window_type = 'desktop',
    own_window_transparent = true,
    own_window_argb_visual = true,
    own_window_argb_value = 0,
    update_interval = 1.0,
    use_xft = true,
}

conky.text = [[
${color 89B4FA}SYSTEM ${hr 2}
${color CDD6F4}OS: ${alignr}${color A6E3A1}${execi 86400 cat /etc/os-release | grep PRETTY_NAME | cut -d '"' -f2}
${color CDD6F4}Kernel: ${alignr}${color A6E3A1}${kernel}
${color CDD6F4}Uptime: ${alignr}${color A6E3A1}${uptime}

${color 89B4FA}CPU ${hr 2}
${color CDD6F4}Usage: ${alignr}${color A6E3A1}${cpu}%
${color CDD6F4}${cpubar 8}

${color 89B4FA}MEMORY ${hr 2}
${color CDD6F4}Used: ${alignr}${color A6E3A1}${mem} / ${memmax}
${color CDD6F4}${membar 8}

${color 89B4FA}NETWORK ${hr 2}
${color CDD6F4}↑ ${upspeed} ${alignr}${color CDD6F4}↓ ${downspeed}
]]
```

**Auto-start Conky:**
Add to KDE autostart: System Settings → Autostart → Add Application → `conky -c ~/.config/conky/conky.conf`

### KDE Plasma Widgets on Desktop

Right-click desktop → Add Widgets. Desktop widgets include:
- Analog clock, digital clock
- Notes (sticky notes)
- Weather widget
- System Load Viewer
- Folder View (files on desktop)
- Picture Frame

---

## 24. Latte Dock (Deprecated) vs. Native Panel Alternatives

### Latte Dock Status

Latte Dock is **no longer actively maintained** and broken on Plasma 6. For Plasma 5, it remains available, but for Plasma 6 you should use alternatives.

```bash
# Plasma 5 only:
yay -S latte-dock
```

### Plasma 6 Alternatives to Latte

**1. Native Floating Panel**
KDE Plasma 6's native panel now supports floating mode (gap from screen edge). Enable in Edit Mode → Floating toggle. Combine with Panel Colorizer widget for transparency and blur.

**2. Panel Colorizer Widget**
```bash
# Install from KDE Store or:
yay -S plasma-panel-colorizer
```

This widget allows per-panel:
- Background color with opacity
- Gradient backgrounds
- Blur behind panel
- Custom radius

**3. Plank Dock**
```bash
sudo pacman -S plank
```
Simple macOS-like dock. Less customizable than Latte but works on Plasma 6.

**4. Nwg-Dock**
A Wayland-native dock, works well with KDE on Wayland:
```bash
yay -S nwg-dock-hyprland  # or nwg-dock
```

---

## 25. Login Screen (SDDM) Theming

SDDM is KDE's default display manager. It has its own theming system.

### Installing SDDM Themes

```bash
# Theme location:
/usr/share/sddm/themes/

# Install a theme (e.g., Sugar Candy):
yay -S sddm-theme-sugar-candy-git

# Or manually:
sudo cp -r MySDDMTheme /usr/share/sddm/themes/
```

### Setting SDDM Theme

System Settings → Colors & Themes → Login Screen (SDDM) → select theme

Or edit `/etc/sddm.conf`:
```ini
[Theme]
Current=sugar-candy
```

### Popular SDDM Themes

| Theme | Style |
|-------|-------|
| Sugar Candy | Elegant, blurred wallpaper |
| Chili for KDE | Minimalist |
| Catppuccin SDDM | Pastel palette |
| Where Is My SDDM Theme | Minimal, clean |
| aerial-sddm | macOS Aerial-inspired |
| Tokyo Night SDDM | Dark, neon |

### SDDM Configuration

Edit `/etc/sddm.conf.d/kde_settings.conf`:
```ini
[Autologin]
Relogin=false
Session=
User=

[General]
HaltCommand=/usr/bin/systemctl poweroff
RebootCommand=/usr/bin/systemctl reboot

[Theme]
Current=your-theme
CursorTheme=Bibata-Modern-Classic
Font=Inter,10,-1,5,50,0,0,0,0,0

[Users]
MaximumUid=60000
MinimumUid=1000
```

---

## 26. Plymouth — Boot Splash Screen

Plymouth shows an animation while the system boots (before the login screen appears).

### Installation

```bash
sudo pacman -S plymouth

# Plymouth-KDE integration:
sudo pacman -S plymouth-kcm  # GUI in System Settings
```

### Configuring Plymouth

Edit `/etc/plymouth/plymouthd.conf`:
```ini
[Daemon]
Theme=bgrt
ShowDelay=0
DeviceTimeout=5
```

### Installing Plymouth Themes

```bash
# System themes:
ls /usr/share/plymouth/themes/

# Community themes (AUR):
yay -S plymouth-theme-catppuccin-mocha
yay -S plymouth-theme-spinner-git
yay -S plymouth-theme-rog-git  # ASUS ROG style
```

Set theme:
```bash
sudo plymouth-set-default-theme -R catppuccin-mocha
# -R rebuilds initramfs
```

### Enabling Plymouth in Boot

Edit your kernel cmdline to add `quiet splash`. For systemd-boot, edit your loader entry:
```
/boot/loader/entries/arch.conf
options root=... quiet splash
```

For GRUB, edit `/etc/default/grub`:
```
GRUB_CMDLINE_LINUX_DEFAULT="quiet splash"
```

Then rebuild initramfs:
```bash
sudo mkinitcpio -P  # Arch
sudo dracut --force  # Fedora
sudo update-initramfs -u  # Debian/Ubuntu
```

---

## 27. GRUB Theming

GRUB is the bootloader — visible before Plymouth, before the OS loads.

### Installing GRUB Themes

```bash
# Theme location:
/boot/grub/themes/

# Popular themes (AUR):
yay -S grub-theme-catppuccin-git
yay -S grub-theme-vimix-git
yay -S grub-theme-slaze-git
```

**Manual installation:**
```bash
sudo cp -r MyGRUBTheme /boot/grub/themes/
```

Edit `/etc/default/grub`:
```bash
GRUB_THEME="/boot/grub/themes/catppuccin-mocha-grub-theme/theme.txt"
GRUB_TIMEOUT=3
GRUB_TIMEOUT_STYLE=menu
```

Regenerate GRUB config:
```bash
sudo grub-mkconfig -o /boot/grub/grub.cfg
```

### GRUB Theme Structure

A GRUB theme directory contains:
- `theme.txt` — main config
- PNG images (background, icons)
- Fonts

---

## 28. Audio Visualizers & Eye Candy

### Cava — Terminal Audio Visualizer

```bash
sudo pacman -S cava
```

Config: `~/.config/cava/config`

```ini
[bar]
width = 2
spacing = 1
border_left = 0
border_right = 0
border_top = 0
border_bottom = 0

[color]
gradient = 1
gradient_count = 2
gradient_color_1 = '89b4fa'
gradient_color_2 = 'cba6f7'
```

Run in a terminal pane alongside your music player for visual flair.

### Glava — OpenGL Desktop Visualizer

Renders a visualizer directly on your desktop (like a wallpaper):
```bash
yay -S glava
glava --desktop  # run on desktop
```

### KDE Wallpaper Plugins

Animated / interactive wallpapers via KDE Store:
- **Smart Video Wallpaper** — play video as wallpaper
- **Plasma Splash** — particle effects wallpaper

---

## 29. Color Temperature & Night Mode

### Night Color (KDE Built-in)

System Settings → Display and Monitor → Night Color

- Automatically adjusts screen warmth based on time/location
- Manual temperature slider

### Gammastep / Redshift

For more control:
```bash
sudo pacman -S gammastep  # Wayland
sudo pacman -S redshift   # X11

# Config: ~/.config/gammastep/config.ini
[general]
temp-day=6500
temp-night=3500
brightness-day=1.0
brightness-night=0.8
location-provider=manual

[manual]
lat=40.7
lon=-74.0
```

---

## 30. Dotfile Management & Backup

Once your rice is perfected, you need to manage your dotfiles.

### What to Back Up

```
~/.config/
  kdeglobals
  plasma-org.kde.plasma.desktop-appletsrc
  kwinrc
  kscreenlockerrc
  gtk-3.0/
  gtk-4.0/
  kitty/
  alacritty/
  nvim/
  starship.toml
  fastfetch/
  rofi/
  conky/
  fontconfig/
  kvantum/

~/.local/share/
  plasma/
  icons/       (just note which ones, don't commit binaries)
  color-schemes/
  konsole/

~/.zshrc / ~/.bashrc / ~/.config/fish/
```

### Using Git + Stow (The Standard Method)

```bash
# Create a dotfiles repo:
mkdir ~/dotfiles
cd ~/dotfiles
git init

# Use GNU Stow to create symlinks:
sudo pacman -S stow

# Directory structure:
~/dotfiles/
  zsh/.zshrc
  kitty/.config/kitty/kitty.conf
  nvim/.config/nvim/init.lua
  starship/.config/starship.toml

# Stow creates symlinks from ~ to your repo:
cd ~/dotfiles
stow zsh kitty nvim starship
```

### Using chezmoi (Alternative)

```bash
sudo pacman -S chezmoi

# Initialize:
chezmoi init

# Add files:
chezmoi add ~/.config/kitty/kitty.conf
chezmoi add ~/.zshrc

# Edit:
chezmoi edit ~/.zshrc

# Apply:
chezmoi apply

# Push to git:
chezmoi cd && git push
```

### Hosting on GitHub

Create a public repo (e.g., `github.com/yourusername/dotfiles`) and push your dotfiles. Add a README with screenshots — the community loves well-documented rices.

---

## 31. Sharing Your Rice

### Taking Screenshots

```bash
# KDE Screenshot tool:
spectacle

# CLI:
scrot screenshot.png
grim screenshot.png  # Wayland
```

For the classic "rice screenshot," show:
1. Terminal with neofetch/fastfetch
2. A text editor (Neovim preferred)
3. File manager (Dolphin)
4. Your custom panel
5. The wallpaper visible in background

### Where to Share

| Platform | Community |
|----------|-----------|
| **r/unixporn** | The main Linux desktop showcase subreddit |
| **r/kde** | KDE-specific community |
| **KDE Discuss** (discuss.kde.org) | Official KDE forum |
| **KDE Store** (store.kde.org) | Share themes, widgets |
| **GitHub** | Host dotfiles |
| **DeviantArt** | Old-school community, still active |
| **Discord** | r/unixporn Discord, KDE Discord |

### r/unixporn Posting Tips

- Post a full-resolution screenshot
- Include a comment with all components listed (theme, icons, font, terminal, shell, etc.)
- Link to your dotfiles on GitHub
- Use a cohesive color palette throughout
- Don't just post a stock theme — customize it

---

## 32. Troubleshooting Common Ricing Problems

### Plasma Panel Disappears

```bash
plasmashell --replace &
```

### Blur Not Working

- Ensure compositor is running: `qdbus org.kde.KWin /Compositor active`
- Check that Blur effect is enabled in Desktop Effects
- Your Plasma Style must support blur (have `translucent` enabled)
- Your panel/window must have some transparency

### KWin Crashes After Script Install

```bash
# Disable all KWin scripts:
kwriteconfig5 --file kwinrc --group Plugins --key bismuthenabled false
qdbus org.kde.KWin /KWin reconfigure
```

### GTK Apps Look Different from Qt Apps

- Install `kde-gtk-config` and set GTK theme there
- Ensure your GTK theme color scheme matches your KDE color scheme
- Use Catppuccin or other themes that publish both GTK and Qt/Kvantum variants

### Fonts Look Blurry or Pixelated

- Check fontconfig antialiasing settings
- Ensure you're using a Nerd Font or complete font (not missing glyphs)
- On HiDPI: set proper scale and DPI in Display settings

### Icons Not Updating

```bash
# Clear icon cache:
rm -rf ~/.cache/icon-cache.kcache
kbuildsycoca5 --noincremental  # Plasma 5
kbuildsycoca6 --noincremental  # Plasma 6
```

### Flatpak Apps Ignoring Theme

```bash
sudo flatpak override --env=GTK_THEME=YourThemeName
sudo flatpak override --filesystem=$HOME/.themes
sudo flatpak override --filesystem=$HOME/.icons
```

### SDDM Not Using New Theme

```bash
# Check config:
cat /etc/sddm.conf.d/kde_settings.conf

# Verify theme path exists:
ls /usr/share/sddm/themes/

# Test theme directly:
sddm-greeter --test-mode --theme /usr/share/sddm/themes/your-theme
```

### KWin Tiling Gaps Not Showing

With Polonium, gaps require restarting KWin after configuration:
```bash
kwin_wayland --replace &
```

---

## 33. Inspiration & Resources

### Communities

- **r/unixporn** — reddit.com/r/unixporn — the canonical rice showcase
- **r/kde** — reddit.com/r/kde
- **KDE Community Discord** — discord.gg/kde
- **r/unixporn Discord** — discord.gg/unixporn

### Theme Sources

- **KDE Store** — store.kde.org — official KDE theme marketplace
- **Pling** — pling.com — broader theme collection
- **GitHub** — search `kde-theme`, `kvantum-theme`, `plasma-theme`
- **Catppuccin** — github.com/catppuccin — ports for every app
- **Dracula** — draculatheme.com — ports for every app
- **Nord** — nordtheme.com — ports for every app
- **Gruvbox** — github.com/morhetz/gruvbox — warm retro palette

### Learning Resources

- **KDE UserBase Wiki** — userbase.kde.org — official documentation
- **KDE Community Wiki** — community.kde.org
- **ArchWiki: KDE** — wiki.archlinux.org/title/KDE — incredibly detailed
- **ArchWiki: Kvantum** — wiki.archlinux.org/title/Kvantum
- **YouTube:** Search "KDE rice 2024" or "KDE Plasma customization"

### Dotfile Inspiration

Browse GitHub for users posting KDE dotfiles:
```
site:github.com dotfiles kde plasma
```

Notable dotfile repositories to study:
- Search r/unixporn posts tagged [KDE] and look for linked dotfiles

### Color Palette Tools

- **Coolors** — coolors.co — palette generator
- **Catppuccin Color Palette** — catppuccin.com
- **Color Hunt** — colorhunt.co
- **Adobe Color** — color.adobe.com
- **WallHaven Color Search** — wallhaven.cc (filter by color hex)

---

## Quick-Start Checklist

For those who want to get a beautiful rice up fast:

- [ ] Install KDE Plasma on your distro of choice
- [ ] Install Kvantum: `sudo pacman -S kvantum`
- [ ] Pick a color palette (Catppuccin Mocha is a safe, beautiful start)
- [ ] Install matching: Global Theme, Color Scheme, Kvantum Theme, Icon Pack (Papirus-Dark), Cursor (Bibata)
- [ ] Set up a floating panel with Panel Colorizer for blur/transparency
- [ ] Enable KWin Blur and Background Contrast effects
- [ ] Install a Nerd Font and set it everywhere
- [ ] Install Kitty terminal, configure with matching colors
- [ ] Install Zsh + Starship or Oh My Zsh + p10k
- [ ] Install Fastfetch, configure with your system info
- [ ] Set a cohesive wallpaper (use WallHaven, filter by your accent color)
- [ ] Adjust window decorations (Klassy is recommended)
- [ ] Configure SDDM with a matching theme
- [ ] Back up everything to a Git repo

---

*Happy ricing. Your desktop is a reflection of you — make it extraordinary.*
