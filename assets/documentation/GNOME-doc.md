# The Complete Guide to Ricing GNOME Linux
### From a Vanilla Desktop to a Fully Customized, Head-Turning Setup

---

## Table of Contents

1. [What Is Ricing?](#1-what-is-ricing)
2. [Choosing Your Distro and GNOME Version](#2-choosing-your-distro-and-gnome-version)
3. [Essential Tools and Prerequisites](#3-essential-tools-and-prerequisites)
4. [GTK Themes](#4-gtk-themes)
5. [Icon Themes](#5-icon-themes)
6. [Cursor Themes](#6-cursor-themes)
7. [GNOME Shell Themes](#7-gnome-shell-themes)
8. [GNOME Extensions](#8-gnome-extensions)
9. [Fonts](#9-fonts)
10. [Wallpapers](#10-wallpapers)
11. [Terminal Ricing](#11-terminal-ricing)
12. [App-Level Customization](#12-app-level-customization)
13. [Window Manager Tweaks](#13-window-manager-tweaks)
14. [Applying Everything with GNOME Tweaks and dconf](#14-applying-everything-with-gnome-tweaks-and-dconf)
15. [Dotfile Management](#15-dotfile-management)
16. [Advanced: CSS Overrides for GNOME Shell](#16-advanced-css-overrides-for-gnome-shell)
17. [Advanced: Compiling Your Own GTK Theme](#17-advanced-compiling-your-own-gtk-theme)
18. [Inspiration and Communities](#18-inspiration-and-communities)
19. [Troubleshooting Common Issues](#19-troubleshooting-common-issues)
20. [Full Example: A Complete Rice from Scratch](#20-full-example-a-complete-rice-from-scratch)

---

## 1. What Is Ricing?

"Ricing" is the practice of customizing and beautifying your Linux desktop environment. The term originates from the car modding community ("Race Inspired Cosmetic Enhancements") and was adopted by Linux users to describe the art of making a desktop look as aesthetically refined, unique, or minimal as possible.

On GNOME, ricing spans several layers:

- **GTK theming** — controls how apps, buttons, menus, and widgets look
- **GNOME Shell theming** — controls the top bar, dash, overview, and notifications
- **Icon and cursor themes** — visual identity for files and the pointer
- **Extensions** — functional and visual modifications to the Shell
- **Terminal and CLI tools** — fonts, colors, prompts, and TUI apps
- **Fonts** — system-wide typographic consistency
- **Wallpapers and color schemes** — cohesive visual identity

A good rice is cohesive. Every element — from the panel to the file manager to the terminal prompt — should feel like it belongs to the same visual world.

---

## 2. Choosing Your Distro and GNOME Version

Not all GNOME installs are equal. Distros ship different GNOME versions and patch their shells in different ways, which affects theme compatibility.

### Recommended Distros for Ricing GNOME

| Distro | GNOME Version (approx.) | Notes |
|---|---|---|
| **Fedora Workstation** | Latest stable | Clean, unpatched GNOME; ideal for ricing |
| **Arch Linux** | Latest stable | Maximum control, AUR access |
| **EndeavourOS** | Latest stable | Arch-based, beginner-friendlier |
| **openSUSE Tumbleweed** | Rolling | Very recent GNOME, YaST for config |
| **Ubuntu** | Patched GNOME | Ubuntu patches can break some themes |
| **Pop!_OS** | Patched GNOME | Heavily customized; harder to theme cleanly |

> **Recommendation:** Fedora or Arch-based distros are the best canvas for a GNOME rice. Ubuntu and Pop!_OS introduce patches that occasionally conflict with third-party themes and extensions.

### Checking Your GNOME Version

```bash
gnome-shell --version
```

This matters enormously for extensions and shell themes — both are version-specific.

---

## 3. Essential Tools and Prerequisites

Before touching a single theme, install the core tooling.

### 3.1 GNOME Tweaks

GNOME Tweaks is the primary GUI for applying themes, fonts, extensions, and window behavior.

```bash
# Fedora
sudo dnf install gnome-tweaks

# Arch / EndeavourOS
sudo pacman -S gnome-tweaks

# Ubuntu / Debian
sudo apt install gnome-tweaks
```

### 3.2 GNOME Extensions App

The official GNOME Extensions app manages installed extensions.

```bash
# Fedora
sudo dnf install gnome-extensions-app

# Arch
sudo pacman -S gnome-shell-extensions

# Ubuntu
sudo apt install gnome-shell-extensions
```

Also install the **GNOME Shell integration browser extension** for Firefox or Chrome to install extensions from [extensions.gnome.org](https://extensions.gnome.org).

### 3.3 dconf Editor

A powerful low-level settings editor for GNOME.

```bash
# Fedora
sudo dnf install dconf-editor

# Arch
sudo pacman -S dconf-editor

# Ubuntu
sudo apt install dconf-editor
```

### 3.4 git, curl, wget

You'll be cloning theme repos constantly.

```bash
sudo dnf install git curl wget     # Fedora
sudo pacman -S git curl wget       # Arch
sudo apt install git curl wget     # Ubuntu/Debian
```

### 3.5 sassc (for compiling GTK themes)

Required if you want to build themes from source (advanced section).

```bash
sudo dnf install sassc             # Fedora
sudo pacman -S sassc               # Arch
sudo apt install sassc             # Ubuntu/Debian
```

### 3.6 User Theme Extension

To apply custom GNOME Shell themes, you **must** have the **User Themes** extension enabled. Install it from [extensions.gnome.org/extension/19/user-themes](https://extensions.gnome.org/extension/19/user-themes/) or via your package manager.

---

## 4. GTK Themes

GTK (GIMP Toolkit) is the widget library used by most GNOME applications. Themes control colors, borders, shadows, buttons, and every widget element across your apps.

### 4.1 Where Themes Live

| Location | Scope |
|---|---|
| `~/.themes/` | Current user only |
| `~/.local/share/themes/` | Current user only (preferred) |
| `/usr/share/themes/` | System-wide |

Always prefer installing to `~/.local/share/themes/` to keep your rice portable and non-destructive.

### 4.2 Installing a GTK Theme

**Method 1: Manual install from a repo**

```bash
mkdir -p ~/.local/share/themes
cd /tmp
git clone https://github.com/someuser/SomeTheme
cp -r SomeTheme/SomeTheme-variant ~/.local/share/themes/
```

**Method 2: From a .zip or tarball**

```bash
mkdir -p ~/.local/share/themes
tar -xf SomeTheme.tar.gz -C ~/.local/share/themes/
```

### 4.3 Applying the GTK Theme

**Via GNOME Tweaks:**
Open Tweaks → Appearance → Applications → select your theme.

**Via gsettings (CLI):**
```bash
gsettings set org.gnome.desktop.interface gtk-theme "ThemeName"
```

For GTK4 apps (which use libadwaita), additional steps are needed — see Section 4.5.

### 4.4 Top GTK Themes for GNOME

#### Catppuccin
A soothing pastel theme family with four flavors: Latte (light), Frappé, Macchiato, and Mocha (dark).

```bash
git clone https://github.com/catppuccin/gtk ~/.local/share/themes/catppuccin-gtk
```

Follow the repo's install instructions; it uses Python scripts to generate color variants.

#### Gruvbox GTK
Warm retro palette based on the legendary Gruvbox colorscheme.

```bash
git clone https://github.com/Fausto-Korpsvart/Gruvbox-GTK-Theme ~/.local/share/themes/Gruvbox-GTK
```

#### Adw-gtk3
Ports the modern libadwaita (GTK4) look to GTK3 apps so everything looks consistent.

```bash
# Arch AUR
yay -S adw-gtk3

# Manual
git clone https://github.com/lassekongo83/adw-gtk3
cd adw-gtk3 && meson setup build && sudo ninja -C build install
```

This is highly recommended for a clean, modern look.

#### Orchis
Clean material-design-inspired theme with many color variants.

```bash
git clone https://github.com/vinceliuice/Orchis-theme
cd Orchis-theme && ./install.sh -t all
```

#### Marble Shell / Marble GTK
An elegant, polished dark theme with a refined glass-like look.

#### Tokyo Night GTK
Ports the popular Tokyo Night colorscheme (famous in Neovim) to GTK.

### 4.5 GTK4 / Libadwaita (The Hard Part)

Starting with GNOME 42, many apps use **libadwaita**, a library that hardcodes many styles and deliberately resists external theming. This is a significant challenge for ricers.

**For GTK3 themes:** Use `adw-gtk3` as your GTK3 theme so legacy apps match modern apps.

**For libadwaita / GTK4 apps:** You need to override styles via the color palette or CSS.

**Method 1: `ADW_DISABLE_PORTAL=1` (hacky, not recommended)**

**Method 2: Recolor via the Adwaita accent color system**

GNOME 47+ introduced a native accent color picker. Set it:

```bash
gsettings set org.gnome.desktop.interface accent-color 'blue'
# Options: blue, teal, green, yellow, orange, red, pink, purple, slate
```

**Method 3: CSS override for libadwaita**

Create or edit `~/.config/gtk-4.0/gtk.css`:

```css
/* Example: change accent color manually */
@define-color accent_color #89b4fa;
@define-color accent_bg_color #89b4fa;
@define-color accent_fg_color #1e1e2e;
```

**Method 4: Use a theme that ships GTK4 CSS**

Many modern themes like Catppuccin ship `gtk-4.0/` CSS directly. Follow their installation docs to symlink or copy the files:

```bash
# Example for Catppuccin Mocha
mkdir -p ~/.config/gtk-4.0
cp -r ~/.local/share/themes/catppuccin-mocha/gtk-4.0/* ~/.config/gtk-4.0/
```

---

## 5. Icon Themes

Icons define the visual identity of your file manager, application grid, and taskbar. A good icon theme ties the whole look together.

### 5.1 Where Icons Live

| Location | Scope |
|---|---|
| `~/.local/share/icons/` | Current user (preferred) |
| `/usr/share/icons/` | System-wide |

### 5.2 Installing an Icon Theme

```bash
mkdir -p ~/.local/share/icons
git clone https://github.com/someuser/SomeIcons
cp -r SomeIcons/SomeIcons-variant ~/.local/share/icons/
```

### 5.3 Applying the Icon Theme

**Via GNOME Tweaks:**
Tweaks → Appearance → Icons → select theme.

**Via gsettings:**
```bash
gsettings set org.gnome.desktop.interface icon-theme "IconThemeName"
```

### 5.4 Recommended Icon Themes

#### Papirus
The gold standard of GNOME icon themes. Consistent, SVG-based, thousands of icons, dark/light variants.

```bash
# Arch AUR
yay -S papirus-icon-theme

# Ubuntu/Debian
sudo add-apt-repository ppa:papirus/papirus
sudo apt install papirus-icon-theme

# Manual
git clone https://github.com/PapirusDevelopmentTeam/papirus-icon-theme
cd papirus-icon-theme && ./install.sh
```

Papirus also has color variants via `papirus-folders`:

```bash
papirus-folders -C cat-mocha-blue --theme Papirus-Dark
```

#### Tela
Clean, flat icons with multiple color variants.

```bash
git clone https://github.com/vinceliuice/Tela-icon-theme
cd Tela-icon-theme && ./install.sh -a
```

#### Candy Icons
Colorful, rounded icons with a modern macOS-ish flavor.

#### Numix Circle
Classic circular icon theme, great for minimalist setups.

#### Fluent Icons
Microsoft Fluent-inspired, very polished.

```bash
git clone https://github.com/vinceliuice/Fluent-icon-theme
cd Fluent-icon-theme && ./install.sh
```

---

## 6. Cursor Themes

Cursors are often overlooked but instantly elevate a rice when done right.

### 6.1 Where Cursors Live

| Location | Scope |
|---|---|
| `~/.local/share/icons/` | Current user (same folder as icons) |
| `/usr/share/icons/` | System-wide |

### 6.2 Installing a Cursor Theme

```bash
mkdir -p ~/.local/share/icons
tar -xf SomeCursor.tar.gz -C ~/.local/share/icons/
```

### 6.3 Applying the Cursor Theme

**Via GNOME Tweaks:**
Tweaks → Appearance → Cursor → select theme.

**Via gsettings:**
```bash
gsettings set org.gnome.desktop.interface cursor-theme "CursorThemeName"
gsettings set org.gnome.desktop.interface cursor-size 24
```

### 6.4 Recommended Cursor Themes

#### Bibata Modern
Highly popular, clean, multiple color variants (Ice, Fire, Classic).

```bash
# AUR
yay -S bibata-cursor-theme
```

Or download from [pling.com](https://www.pling.com/p/1197198/).

#### Catppuccin Cursors
Matches Catppuccin color schemes perfectly.

```bash
git clone https://github.com/catppuccin/cursors
# Follow install instructions in the repo
```

#### Vimix Cursors
Smooth and elegant.

#### Phinger Cursors
Fun, hand-drawn aesthetic.

#### Nordzy Cursors
Nord palette-based.

---

## 7. GNOME Shell Themes

The Shell theme controls everything that is GNOME-specific: the top bar (panel), the Activities overview, the dash, the app grid, notifications, and the calendar popover.

### 7.1 Prerequisites

The **User Themes** extension **must** be installed and enabled. Without it, GNOME ignores `~/.local/share/themes/` for shell theming.

```bash
# Check if it's installed
gnome-extensions list | grep user-theme
```

### 7.2 Shell Theme Location

Shell themes must be inside a `gnome-shell/` subdirectory within the theme folder:

```
~/.local/share/themes/
└── MyTheme/
    ├── gtk-3.0/
    ├── gtk-4.0/
    └── gnome-shell/
        └── gnome-shell.css
```

### 7.3 Applying a Shell Theme

**Via GNOME Tweaks:**
Tweaks → Appearance → Shell → select theme.

**Via gsettings:**
```bash
gsettings set org.gnome.shell.extensions.user-theme name "ThemeName"
```

### 7.4 Shell Theme Compatibility Warning

Shell themes are **GNOME version specific**. A theme built for GNOME 44 may break on GNOME 46. Always check the theme's README for supported versions.

### 7.5 Recommended Shell Themes

Most GTK themes above include a matching shell theme. Additionally:

- **Marble Shell** — extremely polished glass-like aesthetic
- **Graphite** — clean, rounded, minimal
- **WhiteSur** — macOS Big Sur style
- **Orchis** — matches the GTK theme, many variants

---

## 8. GNOME Extensions

Extensions are the most powerful ricing tool in GNOME. They modify behavior, add UI elements, remove UI elements, and enable things GNOME doesn't offer natively.

### 8.1 Managing Extensions

- **GUI:** Use the GNOME Extensions app or [extensions.gnome.org](https://extensions.gnome.org)
- **CLI:** Use `gnome-extensions` command

```bash
gnome-extensions list              # list all installed
gnome-extensions enable UUID       # enable by UUID
gnome-extensions disable UUID      # disable
gnome-extensions info UUID         # details
```

### 8.2 Essential Extensions for Ricing

#### Appearance / Visual

**Blur my Shell**
Adds blur effects to the panel, overview, and app launcher. One of the most visually impactful extensions.
- UUID: `blur-my-shell@aunetx`
- [extensions.gnome.org/extension/3193/blur-my-shell](https://extensions.gnome.org/extension/3193/blur-my-shell/)

**Rounded Window Corners Reborn**
Adds consistent rounded corners to all windows, including non-GTK apps (Electron, etc.).
- UUID: `rounded-window-corners@fxgn`

**Compiz alike magic lamp effect**
Adds a magic lamp minimize/unminimize animation similar to macOS.

**Burn My Windows**
Adds dramatic window open/close animations (fire, glitch, TV effect, etc.).
- UUID: `burn-my-windows@schneegans.github.com`

#### Panel / Bar

**Just Perfection**
The most comprehensive GNOME Shell tweaker. Lets you hide/show and reposition almost every UI element.
- UUID: `just-perfection-desktop@just-perfection`
- [extensions.gnome.org/extension/3843/just-perfection](https://extensions.gnome.org/extension/3843/just-perfection/)

Key options:
- Hide the panel in overview
- Remove panel button, Activities button, or app menu
- Adjust panel height and padding
- Change overview layout

**Dash to Panel**
Converts the GNOME dash into a full taskbar (Windows-like). Many configuration options.
- UUID: `dash-to-panel@jderose9.github.com`

**Dash to Dock**
Converts the dash into a persistent dock (macOS-like). Choose from bottom, left, or right.
- UUID: `dash-to-dock@micxgx.gmail.com`

**Panel Date Format**
Lets you customize the clock format in the panel (e.g., `%A, %B %d  %H:%M`).

**Caffeine**
Adds a toggle to prevent the screen from sleeping — useful during presentations or videos.

#### Functionality

**Pop Shell**
Tiling window management from System76. Adds keyboard-driven tiling to GNOME.
- UUID: `pop-shell@system76.com`

**gTile**
Grid-based tiling, very configurable.

**Unite**
Moves window titles and controls into the top bar to save vertical space.

**AppIndicator and KStatusNotifierItem Support**
Adds system tray icon support (essential if you use apps like Discord, Dropbox, etc.).
- UUID: `appindicatorsupport@rgcjonas.gmail.com`

**Clipboard Indicator**
Clipboard history manager accessible from the panel.

**GSConnect**
KDE Connect integration — sync your Android phone with GNOME (share files, notifications, clipboard, remote input).

**Tactile**
Keyboard-driven window snapping via a visual overlay.

**Window Gestures**
Multi-finger touchpad gestures for switching workspaces and windows.

### 8.3 Extension Configuration

Most extensions have a gear icon in the Extensions app. You can also configure them via `dconf`:

```bash
# Example: configure Blur my Shell
dconf write /org/gnome/shell/extensions/blur-my-shell/panel/blur true
dconf write /org/gnome/shell/extensions/blur-my-shell/panel/sigma 30
```

---

## 9. Fonts

Typography is one of the highest-impact, most-overlooked aspects of a GNOME rice. A beautiful font makes everything feel more intentional.

### 9.1 Font Types in GNOME

GNOME Tweaks exposes four font settings:

| Setting | Purpose |
|---|---|
| **Interface Font** | GTK menus, labels, buttons |
| **Document Font** | Apps like text editors, GNOME Files |
| **Monospace Font** | Terminal, code editors |
| **Legacy Window Title Font** | GTK3 window titlebars |

### 9.2 Installing Fonts

```bash
mkdir -p ~/.local/share/fonts
cp SomeFont.ttf ~/.local/share/fonts/
fc-cache -fv    # refresh font cache
```

Or via your package manager:

```bash
# Fedora
sudo dnf install fira-code-fonts jetbrains-mono-fonts google-noto-fonts-common

# Arch
sudo pacman -S ttf-fira-code ttf-jetbrains-mono noto-fonts

# Ubuntu
sudo apt install fonts-firacode fonts-jetbrains-mono fonts-noto
```

### 9.3 Recommended Fonts

#### Interface / UI Fonts

- **Inter** — extremely clean, designed for UI
- **Geist** (by Vercel) — modern and elegant
- **Nunito** — rounded, friendly
- **DM Sans** — geometric, minimal
- **Sora** — distinctive Japanese-influenced Latin font
- **Bricolage Grotesque** — editorial and expressive

#### Monospace Fonts (Terminal/Code)

- **JetBrains Mono** — excellent ligatures, very legible
- **Fira Code** — the classic ligature font
- **Cascadia Code** — Microsoft's monospace with ligatures
- **Iosevka** — ultra-narrow, highly configurable
- **Maple Mono** — beautiful cursive italics
- **Commit Mono** — neutral and highly readable

#### Font Sources

- [Google Fonts](https://fonts.google.com)
- [Nerd Fonts](https://www.nerdfonts.com) — patched fonts with icons for terminals
- [fontsource.org](https://fontsource.org)

### 9.4 Applying Fonts

**Via GNOME Tweaks:**
Tweaks → Fonts → set each category.

**Via gsettings:**
```bash
gsettings set org.gnome.desktop.interface font-name "Inter 11"
gsettings set org.gnome.desktop.interface document-font-name "Inter 11"
gsettings set org.gnome.desktop.interface monospace-font-name "JetBrains Mono 10"
gsettings set org.gnome.desktop.wm.preferences titlebar-font "Inter Bold 11"
```

### 9.5 Font Rendering

For crisp fonts, configure antialiasing and hinting:

**Via GNOME Tweaks:** Fonts → Antialiasing → Subpixel (for LCD monitors).

**Via gsettings:**
```bash
gsettings set org.gnome.desktop.interface font-antialiasing "rgba"
gsettings set org.gnome.desktop.interface font-hinting "slight"
```

---

## 10. Wallpapers

The wallpaper is the backdrop of your entire rice. It should inform your color scheme, not fight against it.

### 10.1 Setting a Wallpaper

**Via GNOME Settings:**
Settings → Background → add/select image.

**Via gsettings:**
```bash
gsettings set org.gnome.desktop.background picture-uri "file:///home/user/Pictures/wallpaper.jpg"
gsettings set org.gnome.desktop.background picture-uri-dark "file:///home/user/Pictures/wallpaper-dark.jpg"
gsettings set org.gnome.desktop.background picture-options "zoom"
# Options: none, wallpaper, centered, scaled, stretched, zoom, spanned
```

### 10.2 Dynamic and Auto-Changing Wallpapers

**Variety** — wallpaper changer with slideshow, download from sources, Unsplash, etc.

```bash
sudo dnf install variety       # Fedora
sudo pacman -S variety         # Arch AUR
sudo apt install variety       # Ubuntu
```

**GNOME XML wallpapers** — GNOME natively supports timed/dynamic wallpapers via XML files:

```xml
<background>
  <starttime><year>2024</year><month>01</month><day>01</day>
    <hour>6</hour><minute>0</minute><second>0</second>
  </starttime>
  <static>
    <duration>7200</duration>
    <file>/home/user/Pictures/morning.jpg</file>
  </static>
  <transition>
    <duration>300</duration>
    <from>/home/user/Pictures/morning.jpg</from>
    <to>/home/user/Pictures/evening.jpg</to>
  </transition>
</background>
```

Save as `~/.local/share/backgrounds/dynamic.xml` and set via gsettings.

### 10.3 Wallpaper Sources

- [Unsplash](https://unsplash.com) — high-quality photography (free)
- [WallHaven](https://wallhaven.cc) — massive community collection
- [Reddit r/unixporn](https://reddit.com/r/unixporn) — themed wallpapers from ricers
- [Artstation](https://artstation.com) — artistic digital art
- [PixelMator/Canva/Designer] — create your own matching wallpapers
- [Catppuccin Wallpapers](https://github.com/catppuccin/wallpapers) — palette-matched

### 10.4 Color-Matching Wallpapers to Your Theme

Use **Pywal** to automatically generate a color scheme from your wallpaper:

```bash
pip install pywal
wal -i ~/Pictures/wallpaper.jpg
```

Pywal generates a color palette and applies it to supported terminals, Rofi, dunst, and more. Use community templates to extend it to other apps.

---

## 11. Terminal Ricing

The terminal is the heart of any Unix rice. A beautiful terminal signals mastery and sets the tone for the whole setup.

### 11.1 Choosing a Terminal Emulator

| Terminal | Notes |
|---|---|
| **GNOME Terminal** | Default; theming via profiles |
| **Alacritty** | GPU-accelerated, config file-based |
| **Kitty** | GPU-accelerated, very extensible |
| **Foot** | Wayland-native, lightweight |
| **WezTerm** | GPU-accelerated, Lua config, tabs, splits |
| **Ghostty** | Blazing fast, modern config format |

For ricing purposes, **Kitty**, **Alacritty**, **WezTerm**, or **Ghostty** are recommended for their config-file-based customization.

### 11.2 Kitty Configuration

Config file: `~/.config/kitty/kitty.conf`

```ini
# Font
font_family      JetBrains Mono
font_size        12.0

# Window padding
window_padding_width 16

# Transparency
background_opacity 0.92

# Colors (Catppuccin Mocha example)
background            #1e1e2e
foreground            #cdd6f4
cursor                #f5e0dc
color0                #45475a
color1                #f38ba8
color2                #a6e3a1
color3                #f9e2af
color4                #89b4fa
color5                #f5c2e7
color6                #94e2d5
color7                #bac2de
color8                #585b70
color9                #f38ba8
color10               #a6e3a1
color11               #f9e2af
color12               #89b4fa
color13               #f5c2e7
color14               #94e2d5
color15               #a6adc8

# Tab bar
tab_bar_style powerline
tab_powerline_style slanted

# Hide window decorations
hide_window_decorations yes
```

Pre-made Kitty color themes: [github.com/dexpota/kitty-themes](https://github.com/dexpota/kitty-themes)

### 11.3 Alacritty Configuration

Config file: `~/.config/alacritty/alacritty.toml`

```toml
[font]
normal = { family = "JetBrains Mono", style = "Regular" }
size = 12.0

[window]
padding = { x = 16, y = 16 }
opacity = 0.92
decorations = "none"

[colors.primary]
background = "#1e1e2e"
foreground = "#cdd6f4"
```

### 11.4 Shell Prompt: Starship

Starship is a minimal, fast, infinitely customizable prompt written in Rust. Works in any shell (bash, zsh, fish).

**Install:**
```bash
curl -sS https://starship.rs/install.sh | sh
```

**Add to shell:**
```bash
# ~/.bashrc or ~/.zshrc
eval "$(starship init zsh)"
```

**Config:** `~/.config/starship.toml`

```toml
format = """
[╭─](bold green)$os$username$directory$git_branch$git_status
[╰─](bold green)$character"""

[os]
disabled = false
style = "bold blue"

[directory]
style = "bold cyan"
truncation_length = 3

[git_branch]
format = "[$symbol$branch]($style) "
style = "bold purple"

[character]
success_symbol = "[❯](bold green)"
error_symbol = "[❯](bold red)"
```

### 11.5 Shell: Zsh + Oh My Zsh / Zinit

Zsh with plugins adds autocompletion, syntax highlighting, and history search.

```bash
# Install Zsh
sudo dnf install zsh && chsh -s $(which zsh)

# Oh My Zsh
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"

# Essential plugins (add to ~/.zshrc plugins=(...))
# zsh-autosuggestions, zsh-syntax-highlighting, z, fzf
```

### 11.6 CLI Tools That Look Great

Replacing standard tools with modern alternatives dramatically improves terminal aesthetics.

| Old Tool | Replacement | Install |
|---|---|---|
| `ls` | **eza** | `cargo install eza` |
| `cat` | **bat** | `sudo pacman -S bat` |
| `find` | **fd** | `sudo pacman -S fd` |
| `grep` | **ripgrep (rg)** | `sudo pacman -S ripgrep` |
| `top/htop` | **btop** | `sudo pacman -S btop` |
| `cd` | **zoxide** | `cargo install zoxide` |
| `du` | **dust** | `cargo install du-dust` |
| `diff` | **delta** | `cargo install git-delta` |

**Neofetch / Fastfetch** — display system info in a pretty format:

```bash
sudo pacman -S fastfetch
fastfetch   # runs on terminal open
```

Configure: `~/.config/fastfetch/config.jsonc`

---

## 12. App-Level Customization

### 12.1 Firefox

Firefox can be extensively themed to match your rice.

**Via Firefox Color:**
Install the [Firefox Color extension](https://color.firefox.com) and create a palette matching your theme.

**Via userChrome.css:**

Enable `toolkit.legacyUserProfileCustomizations.stylesheets` in `about:config`, then create:
`~/.mozilla/firefox/PROFILE/chrome/userChrome.css`

```css
/* Hide tab bar (useful with tree-style tabs) */
#TabsToolbar { visibility: collapse !important; }

/* Rounded UI */
.tabbrowser-tab { border-radius: 8px !important; }
```

Community resources: [github.com/hakimel/CSS](https://github.com/hakimel/CSS), r/FirefoxCSS.

**Arc Browser / Zen Browser** — Zen is a Firefox fork with beautiful built-in theming.

### 12.2 VSCode / Cursor / Neovim

**VSCode:** Install a theme matching your palette:
- Catppuccin for VSCode
- Tokyo Night
- Gruvbox Material
- Rosé Pine

**Neovim:** A fully themed Neovim setup is a rice unto itself. Popular color schemes:
- `catppuccin/nvim`
- `folke/tokyonight.nvim`
- `ellisonleao/gruvbox.nvim`
- `rose-pine/neovim`

Use a plugin manager like **lazy.nvim** and pair with **lualine.nvim** for a themed statusline.

### 12.3 GNOME Files (Nautilus)

Nautilus picks up your GTK theme automatically. For additional tweaks:
- Install the **Nautilus File Preview** extension for quick previews
- Use custom emblems and folder colors with **Folder Color** (uses Papirus integration)

### 12.4 Theming Electron Apps (Discord, Obsidian, etc.)

Electron apps embed their own Chromium rendering engine and largely ignore GTK themes.

**Discord:**
Use **Vencord** or **BetterDiscord** with a theme matching your palette. Catppuccin has an official Discord theme.

```bash
# Install Vencord
sh -c "$(curl -sS https://raw.githubusercontent.com/Vendicated/VencordInstaller/main/install.sh)"
```

**Obsidian:**
Obsidian has a built-in community theme store. Search for Catppuccin, Rosé Pine, or Gruvbox.

**VS Code:**
Fully supported via the Extensions marketplace.

---

## 13. Window Manager Tweaks

### 13.1 Window Decorations (Titlebars)

For GTK3 apps, you can control the titlebar via the theme. For a minimal look:

**Remove titlebars on maximized windows:**
Use the **Unite** extension to merge the titlebar into the panel.

**Custom button layout:**
```bash
# Move buttons to the left (macOS style)
gsettings set org.gnome.desktop.wm.preferences button-layout "close,minimize,maximize:"

# Buttons on the right (default)
gsettings set org.gnome.desktop.wm.preferences button-layout ":minimize,maximize,close"

# No buttons (very minimal)
gsettings set org.gnome.desktop.wm.preferences button-layout ":"
```

### 13.2 Animations

Speed up or slow down GNOME animations:

```bash
# Disable animations
gsettings set org.gnome.desktop.interface enable-animations false

# Change animation speed (gsettings doesn't expose this directly)
# Use Looking Glass (Alt+F2 → type 'lg') for runtime tweaks
```

With the **Just Perfection** extension, you can scale animation speed.

### 13.3 Workspaces

```bash
# Dynamic workspaces
gsettings set org.gnome.mutter dynamic-workspaces true

# Fixed number of workspaces
gsettings set org.gnome.mutter dynamic-workspaces false
gsettings set org.gnome.desktop.wm.preferences num-workspaces 4

# Workspaces span all monitors
gsettings set org.gnome.mutter workspaces-only-on-primary false
```

### 13.4 Window Snapping and Tiling

GNOME 45+ includes basic edge tiling. For full tiling:

- **Pop Shell** — keyboard-driven auto tiling
- **gTile** — grid-based manual tiling
- **Paper WM** — scrolling tiling (like a paper roll)
- **Tactile** — snap windows to a visual grid overlay

---

## 14. Applying Everything with GNOME Tweaks and dconf

### 14.1 GNOME Tweaks Overview

GNOME Tweaks is your central control panel. Relevant tabs:

- **Appearance** — GTK theme, icon theme, cursor theme, shell theme, background
- **Fonts** — all font settings with antialiasing and hinting
- **Keyboard & Mouse** — pointer speed, middle click paste
- **Windows** — attach modal dialogs, edge tiling, resize with right-click
- **Workspaces** — static vs dynamic
- **Extensions** — quick toggle for all installed extensions

### 14.2 Bulk Apply with dconf

`dconf` is the backend for all GNOME settings. You can dump your entire config and restore it elsewhere — this is the foundation of portable rices.

**Backup your settings:**
```bash
dconf dump / > ~/gnome-settings-backup.dconf
```

**Restore settings:**
```bash
dconf load / < ~/gnome-settings-backup.dconf
```

**Export just appearance settings:**
```bash
dconf dump /org/gnome/desktop/ > desktop-settings.dconf
dconf dump /org/gnome/shell/ > shell-settings.dconf
```

**Set a specific key:**
```bash
dconf write /org/gnome/desktop/interface/gtk-theme "'Catppuccin-Mocha-Standard-Blue-Dark'"
```

**Read a key:**
```bash
dconf read /org/gnome/desktop/interface/gtk-theme
```

### 14.3 gsettings vs dconf

`gsettings` is the high-level API; `dconf` is the low-level storage. Both write to the same backend. Use `gsettings` for standard settings and `dconf` for extension-specific or undocumented paths.

```bash
# gsettings example
gsettings set org.gnome.desktop.interface icon-theme "Papirus-Dark"

# dconf equivalent
dconf write /org/gnome/desktop/interface/icon-theme "'Papirus-Dark'"
```

---

## 15. Dotfile Management

A rice is only as good as its reproducibility. Dotfiles are the config files that define your entire setup.

### 15.1 What to Track

```
~/.config/
├── alacritty/alacritty.toml
├── kitty/kitty.conf
├── starship.toml
├── fastfetch/config.jsonc
├── gtk-3.0/settings.ini
├── gtk-4.0/gtk.css
├── nvim/
├── fish/ or zsh/
└── hypr/ (if using Hyprland alongside)

~/.local/share/gnome-shell/extensions/   # custom extension configs
~/.bashrc or ~/.zshrc
~/.profile
```

### 15.2 GNU Stow (Symlink Manager)

GNU Stow creates symlinks from a dotfiles repo to their expected locations.

```bash
sudo pacman -S stow

# Directory structure
~/dotfiles/
├── kitty/
│   └── .config/kitty/kitty.conf
├── starship/
│   └── .config/starship.toml
└── zsh/
    └── .zshrc

# Apply
cd ~/dotfiles
stow kitty starship zsh
```

### 15.3 Chezmoi (Advanced Dotfile Manager)

Chezmoi handles secrets, templates, and machine-specific configs.

```bash
sh -c "$(curl -fsLS get.chezmoi.io)"
chezmoi init
chezmoi add ~/.config/kitty/kitty.conf
chezmoi cd        # enter the dotfile repo
```

### 15.4 Git for Dotfiles

```bash
cd ~/dotfiles
git init
git add .
git commit -m "Initial rice: Catppuccin Mocha"
git remote add origin https://github.com/youruser/dotfiles
git push -u origin main
```

Document your rice in the README with screenshots, software list, and install instructions.

---

## 16. Advanced: CSS Overrides for GNOME Shell

GNOME Shell is rendered using CSS. You can override virtually anything by editing or appending CSS.

### 16.1 Finding Shell CSS

The default shell CSS lives in:
```
/usr/share/gnome-shell/gnome-shell.css
```

**Never edit this file directly** — it gets overwritten on updates.

### 16.2 User Theme Override

When the User Themes extension is active and a shell theme is selected, GNOME loads:
```
~/.local/share/themes/YourTheme/gnome-shell/gnome-shell.css
```

You can append your own rules at the bottom of `gnome-shell.css` in your theme.

### 16.3 Inspecting Shell Elements

Open the **Looking Glass** debugger:
- Press `Alt+F2`, type `lg`, press Enter

In the Picker tab, click any shell element to inspect its CSS class and live-edit styles.

### 16.4 Useful CSS Snippets

```css
/* Make the top panel transparent */
#panel {
  background-color: transparent;
  background-gradient-start: transparent;
  background-gradient-end: transparent;
}

/* Rounded corners on notifications */
.notification-banner {
  border-radius: 16px;
}

/* Remove panel background completely */
#panel.solid {
  background-color: rgba(0,0,0,0) !important;
}

/* Customize the dash */
.dash-background {
  background-color: rgba(30, 30, 46, 0.8);
  border-radius: 20px;
}

/* Calendar popup rounding */
.calendar-month-header {
  border-radius: 12px 12px 0 0;
}
```

---

## 17. Advanced: Compiling Your Own GTK Theme

For complete control, build a GTK theme from scratch.

### 17.1 Understanding GTK Theme Structure

```
MyTheme/
├── index.theme              # metadata
├── gtk-3.0/
│   ├── gtk.css              # compiled CSS
│   ├── gtk-dark.css
│   └── assets/              # PNGs for buttons, etc.
├── gtk-4.0/
│   └── gtk.css
└── gnome-shell/
    └── gnome-shell.css
```

### 17.2 Starting from a Theme Like Adwaita

```bash
git clone https://gitlab.gnome.org/GNOME/gtk
cd gtk/gtk/theme/Adwaita
```

The source is written in SCSS (Sassy CSS) and compiled to CSS using `sassc`.

### 17.3 Compile a Modified Theme

```bash
# Clone a theme with SCSS source (e.g., Graphite)
git clone https://github.com/vinceliuice/Graphite-gtk-theme
cd Graphite-gtk-theme

# Edit SCSS variables
nano src/_sass/gtk/_variables.scss

# Run install script (compiles and installs)
./install.sh --color dark --accent pink
```

### 17.4 Editing Color Variables

Most themes expose color variables in a `_colors.scss` or `_variables.scss` file:

```scss
// Example variable file
$accent_color: #89b4fa;      // blue (Catppuccin)
$bg_color: #1e1e2e;          // base
$fg_color: #cdd6f4;          // text
$header_bg: #181825;         // mantle
```

Change these, recompile with `sassc`, and your theme reflects the new palette.

---

## 18. Inspiration and Communities

### 18.1 Communities

- **[r/unixporn](https://reddit.com/r/unixporn)** — the premier Linux rice sharing community. Browse for inspiration and find dotfile links in every post.
- **[r/gnome](https://reddit.com/r/gnome)** — GNOME-specific discussion
- **[pling.com / gnome-look.org](https://gnome-look.org)** — massive repository of themes, icons, and cursors
- **Discord servers:** Catppuccin, Hyprland, r/unixporn all have active servers
- **GitHub:** Search for `dotfiles` and filter by language/topic

### 18.2 Popular Ricers to Follow

Browse GitHub for users who maintain public dotfiles with screenshots. Many post on r/unixporn with dotfile links.

### 18.3 Color Scheme Resources

- [Catppuccin](https://github.com/catppuccin/catppuccin) — ports for almost every app
- [Rosé Pine](https://rosepinetheme.com) — elegant, muted, natural
- [Gruvbox](https://github.com/morhetz/gruvbox) — warm retro
- [Tokyo Night](https://github.com/enkia/tokyo-night-vscode-theme) — cool blues and purples
- [Nord](https://nordtheme.com) — arctic blue
- [Dracula](https://draculatheme.com) — vibrant purple/pink
- [Everforest](https://github.com/sainnhe/everforest) — green-tinted natural tones
- [Kanagawa](https://github.com/rebelot/kanagawa.nvim) — inspired by Japanese art

---

## 19. Troubleshooting Common Issues

### GTK Theme Not Applying

- Ensure the theme folder is in `~/.local/share/themes/` or `~/.themes/`
- Check the theme supports your GTK version (`gtk-3.0` vs `gtk-4.0`)
- For GTK4/libadwaita apps, copy the `gtk-4.0` CSS to `~/.config/gtk-4.0/`
- Restart GNOME Shell: `Alt+F2 → r → Enter` (X11) or log out/in (Wayland)

### Shell Theme Not Applying

- Confirm User Themes extension is installed and enabled
- The theme must have a `gnome-shell/gnome-shell.css` file
- Shell theme must match your GNOME version
- Check extension conflicts with Just Perfection or Blur my Shell

### Icons Not Updating

```bash
# Rebuild icon cache
gtk-update-icon-cache ~/.local/share/icons/YourIconTheme/
```

Log out and back in if icons still don't update.

### Extension Not Working After Update

GNOME extensions are version-locked. After a GNOME update:
1. Check the extension's page on extensions.gnome.org for an updated version
2. Or use **Extension Manager** app (from Flathub) — it has an "Update" button per extension
3. As a workaround, edit the extension's `metadata.json` to include your GNOME version (may cause instability)

### Transparency / Blur Not Working on Wayland

Some transparency effects require compositor support. On Wayland with Mutter (stock GNOME):
- Blur my Shell should work on GNOME 43+
- True window transparency requires the compositor to support it
- Some effects are X11-only; check extension documentation

### Fonts Look Blurry

```bash
gsettings set org.gnome.desktop.interface font-antialiasing "rgba"
gsettings set org.gnome.desktop.interface font-hinting "slight"
```

Also ensure you're using the correct DPI for your monitor. For HiDPI:
```bash
gsettings set org.gnome.desktop.interface text-scaling-factor 1.25
```

### Theme Breaks After System Update

GTK and GNOME Shell updates can break themes. Solutions:
- Check the theme repo's GitHub Issues page
- Roll back to a previous theme version
- Switch to a more actively maintained theme
- Rebuild the theme from source against the new GTK version

---

## 20. Full Example: A Complete Rice from Scratch

Here is a step-by-step walkthrough of building a complete Catppuccin Mocha rice on Fedora.

### Step 1: Install Prerequisites

```bash
sudo dnf install gnome-tweaks gnome-extensions-app dconf-editor git curl sassc
```

### Step 2: Install User Themes Extension

Visit https://extensions.gnome.org/extension/19/user-themes/ and toggle it on.

### Step 3: Install GTK Theme (Catppuccin)

```bash
mkdir -p ~/.local/share/themes
cd /tmp
git clone https://github.com/catppuccin/gtk catppuccin-gtk
cd catppuccin-gtk
pip install --user pywal
python install.py -l mocha -a blue
```

This installs `Catppuccin-Mocha-Standard-Blue-Dark` and similar variants.

### Step 4: Install GTK4 / Libadwaita CSS

```bash
mkdir -p ~/.config/gtk-4.0
cp -r ~/.local/share/themes/Catppuccin-Mocha-Standard-Blue-Dark/gtk-4.0/* ~/.config/gtk-4.0/
```

### Step 5: Install adw-gtk3

```bash
git clone https://github.com/lassekongo83/adw-gtk3
cd adw-gtk3 && meson setup build && sudo ninja -C build install
```

Apply the dark variant as your GTK3 theme to match GTK4 apps.

### Step 6: Install Papirus Icons

```bash
sudo dnf install papirus-icon-theme
papirus-folders -C cat-mocha-blue --theme Papirus-Dark
```

### Step 7: Install Bibata Cursor

Download from https://github.com/ful1e5/Bibata_Cursor/releases and extract to `~/.local/share/icons/`.

### Step 8: Apply Everything via GNOME Tweaks

Open Tweaks:
- Appearance → Applications → `adw-gtk3-dark`
- Appearance → Icons → `Papirus-Dark`
- Appearance → Cursor → `Bibata-Modern-Ice`
- Appearance → Shell → `Catppuccin-Mocha-Standard-Blue-Dark`
- Fonts → Interface → `Inter 11`
- Fonts → Monospace → `JetBrains Mono 10`
- Fonts → Antialiasing → Subpixel

### Step 9: Install and Configure Extensions

Install via extensions.gnome.org:
- **Blur my Shell** — set panel blur sigma to 20, brightness 0.8
- **Just Perfection** — hide panel in overview, set activity button label to blank
- **Rounded Window Corners Reborn** — border radius 12px
- **AppIndicator Support** — for system tray
- **Dash to Dock** — position bottom, icon size 48

### Step 10: Set Up Terminal (Kitty)

```bash
sudo dnf install kitty
mkdir -p ~/.config/kitty
```

Write `~/.config/kitty/kitty.conf` with the Catppuccin Mocha palette (see Section 11.2).

### Step 11: Install Starship Prompt

```bash
curl -sS https://starship.rs/install.sh | sh
echo 'eval "$(starship init bash)"' >> ~/.bashrc
```

Write a Starship config with your preferred format.

### Step 12: Install fastfetch

```bash
sudo dnf install fastfetch
```

Configure `~/.config/fastfetch/config.jsonc` to show your system info with ASCII art.

### Step 13: Set a Matching Wallpaper

Download a Catppuccin wallpaper from https://github.com/catppuccin/wallpapers and set it:

```bash
gsettings set org.gnome.desktop.background picture-uri "file:///home/$(whoami)/Pictures/catppuccin-mocha.jpg"
```

### Step 14: Backup Your Dotfiles

```bash
mkdir -p ~/dotfiles
cp -r ~/.config/kitty ~/dotfiles/
cp -r ~/.config/gtk-4.0 ~/dotfiles/
cp ~/.bashrc ~/dotfiles/
dconf dump / > ~/dotfiles/gnome-settings.dconf

cd ~/dotfiles
git init && git add . && git commit -m "Catppuccin Mocha GNOME rice"
```

### Step 15: Take a Screenshot and Share

```bash
# Take a screenshot
gnome-screenshot -f ~/Pictures/rice-$(date +%Y%m%d).png

# Or use the PrtScr key and upload to Imgur, then post to r/unixporn
```

---

## Final Notes

A great rice is never truly finished — it evolves as you discover new tools, themes, and workflows. Start with a color palette you love, build outward from the terminal and shell, and iterate. Consistency is the key: every element should look like it belongs to the same world.

Document everything. Your future self (and the community) will thank you.

Happy ricing. 🎨

---

*Guide covers GNOME 44–47 as of 2025. Extension compatibility and theme availability change frequently; always check upstream repositories for the latest instructions.*