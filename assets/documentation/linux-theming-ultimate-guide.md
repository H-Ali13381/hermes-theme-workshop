# Linux & Theming — The Ultimate Guide

**Source:** [YouTube – diinki](https://www.youtube.com/watch?v=jFz5gLqv-FM)  
**Channel:** diinki  
**Duration:** 34:34  
**Description:** A full guide to Linux ricing for all skill levels, covering Sway, Waybar, Wofi, Kitty, GTK, and EWW on Arch / Endeavour OS.

> **Note:** Transcribed from auto-generated captions. Technical terms corrected where identifiable.

---

## Introduction

I'm Dinki and today I'm going to teach you a few things about style.

The Linux ecosystem is ever growing and so is its user base. It's no longer just for the few or for the niche. No, Linux is for everyone. It is also for you. And the longer you do use Linux, you will realize it has an immense ability to be customized.

In this guide, I'm going to teach you how to make a Linux rice that looks like this. And most importantly, teach you how it's done from scratch. That way, you'll be able to gain inspiration and the knowledge required to continue ricing your operating system and make things look nice and personal.

This video will have many chapters as some of the things I'm going to go through are things that you might already know. Although I suggest sticking along — you might learn a thing or two still.

---

## Chapter 1: What is Linux?

An entire operating system is made from multiple components. One such component is the **kernel**. The kernel is what facilitates communication between your actual physical computer and the software that runs on top.

Many groups of people and organizations have used the Linux kernel to make entire operating systems. These are called **Linux distros** or distributions for short. A few examples are Arch, Endeavour OS, Debian, Fedora. One distinction that's important: Linux is open source and as such it's completely free.

When you install a Linux distro such as Ubuntu, you will get to choose to install it with a **desktop environment**, or DE for short. There are a few different kinds of DEs — examples are GNOME, KDE, XFCE, COSMIC, and so on. Really, a DE is a collection of components that make up an operating system front end: the core windowing system, a login manager, file explorer, settings menu, and so on.

But when we speak of **ricing Linux**, we usually speak of handpicking all of these components ourselves — including the core windowing system — such as Wayland or the X windowing system. For that we don't want complete desktop environments. We want **tiling window managers**. One of the most important things is of course that you can customize them a lot.

So when we speak of ricing Linux, we speak of installing a tiling window manager of your choice, installing all of the applications you want, and designing everything to look exactly how you want. That's what we're going to do.

---

## Software Stack

For this guide we're going to use **Endeavour OS**. Endeavour is essentially Arch but with a few pre-installed components and a very nice installer — it makes things easy to use.

| Role | Choice |
|---|---|
| Window manager | Sway (Wayland-based) |
| Application launcher | Wofi |
| Custom widgets | EWW |
| Taskbar | Waybar |
| Terminal | Kitty |
| File explorer | Nemo |

All of these are personal choices and preferences. However, they're good to start with and very themable — I recommend trying them if it's your first rice. EWW is the exception; it's kind of difficult to use. We will glance over how to configure it as well.

---

## Installation

If you don't care about the guide and just want to install the rice, you can skip to the Installation chapter. If you're not new to Linux or ricing, you may skip this chapter as it includes great detail.

### Burning the ISO

Go to the Endeavour OS website, download an ISO file, and burn it onto a USB stick. You can do this with:

- **Rufus** (Windows)
- **Balena Etcher** (macOS / Linux)
- The `dd` command (Linux)

You may also use the raw ISO file to create a virtual machine if you don't want to install it permanently.

### First Boot

Plug the USB stick in and boot from it. You'll be greeted by a live view of the OS. Choose to permanently install it, follow the steps, and configure the settings. For this guide we'll start off with the **GNOME desktop environment** — that way I can show you how to install Sway alongside it.

### Installing Software

After installation, run the install command to get most of the necessary software, including Visual Studio Code for editing config files. Some programs cannot be installed with **pacman** and have to be installed from the **Arch User Repository (AUR)** — a community that maintains unofficial software. To make this easy, install the **Yay** AUR helper:

```sh
git clone <yay-url>
cd yay
makepkg -si
```

Use Yay to install EWW as well.

---

## Setting Up the Login Manager

When you restart, you'll be greeted by the login screen. **GDM** is the default login manager that comes with GNOME. We want to be able to switch between GNOME and Sway, so we need a login manager that supports this.

For this video we're going to use **Ly** — it's lightweight and easy to configure. Install it, then:

```sh
sudo systemctl disable gdm
sudo systemctl enable ly
```

### Desktop Session Files

Before restarting, understand something important. In `/usr/share/wayland-sessions/` you'll find config files for GNOME and Sway. These are the files that Ly and other login managers use to detect which desktops are currently available.

Use `cat` to see the contents of the Sway session file — the execution command is simply `sway`. We can edit these files to change how the login manager launches either GNOME or Sway.

**Nvidia note:** If you're on an Nvidia GPU with proprietary drivers, you will need to edit the Sway session file accordingly. Open and edit it with VS Code. AMD GPU or open-source Nvidia driver users don't need to do anything. This step will likely become entirely unnecessary in the future.

After editing, restart. Ly is very simple — you can switch between Sway and GNOME at the login screen.

---

## Sway: Basic Configuration

Before switching to Sway, get a basic configuration file. All programs that need configuration files store them in the `~/.config` directory. Each user has their own separate config files.

Create the Sway directory and config file:

```sh
mkdir ~/.config/sway
touch ~/.config/sway/config
code ~/.config/sway/config
```

Sway stores a default config file at `/etc/sway/config`. Print its contents and copy them into your new config file. Rather than writing everything from scratch, edit this default — it has a bunch of good defaults.

### Key Defaults to Change

Before switching to Sway or ricing, make sure the default applications are set correctly:

- **Terminal:** Change from `foot` → `kitty`
- **App launcher:** Change from `wmenu` → add `wofi` line
- **File explorer:** Create a new variable pointing to `nemo`, add a keybind

```
set $term kitty
set $menu wofi --show drun
set $filemanager nemo
bindsym $mod+e exec $filemanager
```

Note that `Mod+E` is already bound to something else by default — delete that existing binding. Also change the quit keybind from `Mod+Shift+Q` to `Mod+Q` if you prefer.

The **Mod key** is set to the Super key (Windows key) by default — a good default, recommended not to change it.

Read more about Sway config syntax on the i3 documentation page. We've now set the default applications and made Sway at least usable.

---

## Entering Sway: Key Binds

Restart and enter Sway. Essential key binds:

| Key | Action |
|---|---|
| `Mod+Enter` | Open terminal |
| `Mod+D` | Application launcher |
| `Mod+E` | File explorer |
| `Mod+Shift+Space` | Toggle floating mode |
| `Mod+Left click` | Move floating window |
| `Mod+Right click` | Resize floating window |
| `Mod+Q` | Quit window |

A document with all default key binds is available on the GitHub page of this rice.

### Monitor Setup

The system will be laggy and the resolution wrong until you set the default monitor settings. Run `swaymsg -t get_outputs` to get all monitor data. Uncomment the monitor line in the Sway config and replace it with your monitor's details:

```
output <monitor-name> resolution <WxH> position <x,y>
```

For a dual-monitor setup, add two such lines. Save and refresh Sway (`Mod+Shift+C`). The basics of Sway are now set up — not beautiful, but functional.

---

## Ricing: Concept and Aesthetic

This rice will be themed around a **retrofuturistic aesthetic** — modern and simple, but with lots of tasteful elements. All files are available on GitHub.

I selected a few main colors to revolve this rice around and found references for the main idea and theme. After the concept and colors are figured out, it's time to start working on the rice.

---

## Sway: Borders, Gaps & Wallpaper

First, add **gaps** between and outside of the windows:

```
gaps inner 8
gaps outer 4
```

Then add **window borders** — set to 1 pixel each. Refresh to see changes.

### Border Colors

Sway uses this scheme for window border colors (in hexadecimal format):

```
client.<state> <border> <background> <text> <indicator> <child_border>
```

States: `focused`, `focused_inactive`, `unfocused`, `urgent`, `placeholder`. Placeholder shows when moving a window. Some fields (like `text`) only apply if a title bar is enabled.

Refer to the GitHub page for the full color block. The syntax can be figured out by reading the i3 documentation, or by tweaking and observing — that's the best way to learn.

### Wallpaper

The GitHub page for this rice includes custom wallpapers. Set the wallpaper with swaybg:

```
output * bg ~/Pictures/wallpapers/<name>.png fill
```

Modify the path to your downloaded image and refresh.

---

## Kitty: Terminal Theming

Customizing Kitty immediately elevates the entire look. Go to `~/.config/kitty/` (create it if needed):

```sh
mkdir -p ~/.config/kitty
```

Create two files:

- `kitty.conf` — main config (font, opacity, padding, etc.)
- `theme.conf` — color palette

Copy paste the relevant configs from the GitHub page. Most of the code is simply setting colors to adhere to the design system. Key config choice: the **Maple Mono** font.

### Installing Maple Mono

1. Go to the Maple Mono GitHub repository and download the latest version
2. Extract the files and move them to `/usr/share/fonts/` (the global font directory)
3. Since it's global, use `sudo`
4. Refresh the font cache:

```sh
fc-cache -fv
```

The font is now installed and can be used anywhere. After saving the Kitty config files, new terminals will use your color scheme — matching the Sway border colors and wallpaper. It already adds a lot to the rice.

---

## Waybar: Taskbar

On the taskbar we'll track active workspaces, display a clock, a tray bar for active applications, and volume controls.

Sway has a default taskbar. In the Sway config, find the `bar { ... }` block — delete its contents and replace with:

```
bar {
    swaybar_command waybar
}
```

This launches Waybar and refreshes it whenever Sway refreshes.

### Creating the Waybar Config

Create the Waybar directory and files:

```sh
mkdir ~/.config/waybar
touch ~/.config/waybar/config
touch ~/.config/waybar/style.css
```

The `config` file uses **JSON** format and specifies layout, data, and which elements to display. The `style.css` controls the visual appearance.

### Config Structure

Waybar divides the taskbar into three sections: left, center, right:

```json
{
  "position": "top",
  "modules-left": ["sway/workspaces"],
  "modules-center": ["custom/app-launcher"],
  "modules-right": ["network", "battery", "pulseaudio", "tray", "clock"]
}
```

**Workspaces (left):**

```json
"sway/workspaces": {
  "disable-scroll": true,
  "all-outputs": true
}
```

Waybar automatically supports Sway along with other window managers. Read more on the wiki.

**Custom app launcher button (center):**

```json
"custom/app-launcher": {
  "format": " ",
  "on-click": "pkill wofi || wofi --show drun",
  "tooltip": "Application Launcher"
}
```

The `pkill wofi || wofi` pattern makes it a toggle — if Wofi is already open, clicking closes it instead of opening another instance. Add the same toggle behavior to the Sway config keybind for `Mod+D`.

**Right modules:** Network, battery (for laptops), volume, tray bar, clock (24-hour format). These are all natively supported by Waybar — no custom config needed.

### Styling Waybar

Edit `style.css`. CSS knowledge is assumed — refer to the GitHub page for full styles.

Key decisions:
- Font: `Maple Mono`
- Border radius: `9px`
- Background: `transparent` (specified per-element instead)
- General scope groups: clock, tray, workspaces — share the same background color and style
- Transition duration set for smooth animations

Read Waybar configs of different rices on GitHub — they may teach you a lot and inspire you. This suggestion applies to all programs and software you use.

---

## Wofi: Application Launcher

We've chosen **Wofi**, which opens a small window to search for and launch apps. Like Waybar, it uses a CSS-like language for theming.

Create the config directory and files:

```sh
mkdir ~/.config/wofi
touch ~/.config/wofi/config
touch ~/.config/wofi/style.css
```

### Wofi Config

Much simpler than Waybar:

```
terminal=kitty
location=center
width=400
```

Customize to your preference.

### Wofi Style

Like Waybar, add an all-encompassing scope, set the font, and create a scope for all windows with matching colors and design language. By experimenting and matching the style of your design language, you create something cohesive and visually consistent.

---

## GTK Theming

If we open the file explorer, it won't adhere to our theme at all — because it uses the **GTK toolkit**, which has a global theme. File explorers like Nemo are themed according to the current system-wide GTK theme.

### Creating a GTK Theme

We'll use **Themix** (a GUI GTK theme editor) and **dconf** to set the active theme:

```sh
yay -S themix-gui
sudo pacman -S dconf
```

Open Themix, set the colors to match your design language, and export the theme to `~/.themes/`.

Set the active GTK theme using dconf editor:

```sh
dconf-editor
```

Search for `gtk-theme` and enter the name of the theme you created in each field. Open Nemo — the theme is now applied.

### GTK 3 vs GTK 4 Limitation

There's a glaring issue: Themix only creates themes up to **GTK 3**. Many modern apps (Nautilus, volume controls, etc.) use **GTK 4 and greater**. Creating a GTK4 theme requires manually editing files — it's a very extensive task beyond the scope of this video.

A pre-made GTK4 theme that matches this design aesthetic is available in the rice's GitHub repository. Git clone it, drag the GTK theme to `~/.themes/`, and use it. Alternatively, find another GTK4 theme you like.

### Beyond GTK

Applications can be themed further:

- **Spotify** → [Spicetify](https://spicetify.app)
- **Discord** → [Vencord](https://vencord.dev)

A good tip: prioritize GTK-based applications when choosing your software.

---

## EWW: Widgets (Optional)

Strictly speaking, you don't need this step — but it adds a lot. We're going to use **EWW** (ElKowary Widgets) for custom widgets. EWW is a powerful toolkit that lets you create menus, taskbars, and widgets from scratch.

It is, however, daunting at first. It uses a bespoke language (Yuck) alongside a CSS-like language, and setup can be tricky. This section is a quick glance over — download the pre-made EWW configs from the GitHub page.

### Installing EWW Configs

Clone or download the repository from GitHub. Drag the EWW config folder into `~/.config/eww/` (there's no EWW directory by default, so just move the whole folder).

### Launching EWW from Sway

EWW must be launched from Sway. In the EWW config's `scripts/` directory, find `start.sh`. Add this to your Sway config:

```
exec_always ~/.config/eww/scripts/start.sh
```

`exec_always` executes the command every time Sway refreshes.

### Monitor Assignment

After refreshing, you may not see any widgets — this depends on your monitor setup. Open `eww.yuck` in VS Code. Every element has a **monitor tag**:

```lisp
(defwindow my-widget
  :monitor 0  ; <-- change this to your monitor number
  ...)
```

Change the monitor number from 2 to 0 (or whatever your main monitor is) for each widget. After saving, all widgets will move to the correct monitor.

### Default Widgets

The pre-made widgets include:

1. **Date display** — shows the current date
2. **Three shortcut buttons:**
   - Open terminal
   - Open file explorer
   - Toggle power menu

You can change the `anchor` property to reposition widgets (e.g., `center`, `top-right`, etc.).

EWW is bespoke and takes time to understand. Read the config files and documentation, play around with values, and see what changes. That's how you learn — and eventually you'll be able to create more advanced widgets.

---

## Quick Installation Guide

Don't want the full guide? Here's how to install the rice quickly:

**Step 1:** Install your Linux distro of choice.

**Step 2:** Install all necessary software:

```sh
# Adapt the command to your distro's package manager
sudo pacman -S sway waybar wofi kitty nemo ...
```

This rice also supports **Hyprland** if you want to use that instead of Sway.

**Step 3:** Clone the rice repository:

```sh
mkdir ~/repos
git clone <rice-repo-url> ~/repos/diinki-rice
```

Copy all directories from `config/` in the repo to `~/.config/`.

If you want to use the **alternate version** of this rice (a different visual variant), you'll need Hyprland or **SwayFX**. Use the alternate config files in that case.

**Step 4:** Launch Sway or Hyprland:

```sh
sway        # or
Hyprland
```

Use a login manager like Ly, or launch directly from a TTY.

**Step 5:** Edit the config files. Wallpapers and monitor resolution must be configured manually. The config files include detailed comments explaining exactly what to change.

---

## Closing Thoughts

A Linux rice may be a never-ending project. As you grow, you'll customize it more, iterate on it, maybe create a new rice altogether. I recommend always saving your config files to a **GitHub repository** — that way they're never lost.

Linux ricing at its core is design and art. Lots of people publish their own rices online including config files, so you can get a lot of reference for rices and how different software works. You can learn how every single toolkit is used by looking at other people's config files.

I've made a specific video about a rice utilizing a futuristic design language — I recommend watching that video.

Now proceed and live your life in a style of your own choosing. Whether it's the OS that you use, the art that you create, the attire that you adorn, or the words that you utter.
