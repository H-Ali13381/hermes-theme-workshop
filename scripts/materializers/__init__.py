"""Materializer registry — maps app keys to their materializer functions."""

from materializers.kde import materialize_kde
from materializers.kde_extras import (
    materialize_kvantum,
    materialize_plasma_theme,
    materialize_cursor,
    materialize_icon_theme,
    materialize_kde_lockscreen,
    _lockscreen_lnf_for_palette,
)
from materializers.terminals import materialize_kitty, materialize_alacritty, materialize_konsole
from materializers.bars import materialize_waybar, materialize_polybar
from materializers.launchers import materialize_rofi, materialize_wofi
from materializers.notifications import materialize_dunst, materialize_mako, materialize_swaync
from materializers.hyprland import materialize_hyprland, materialize_hyprlock
from materializers.system import (
    materialize_gtk,
    materialize_picom,
    materialize_fastfetch,
    materialize_starship,
    _build_starship_toml,
)
from materializers.gnome import materialize_gnome_shell, materialize_gnome_lockscreen
from materializers.wallpaper import materialize_wallpaper

APP_MATERIALIZERS = {
    # KDE stack
    "kde":            materialize_kde,
    "kvantum":        materialize_kvantum,
    "plasma_theme":   materialize_plasma_theme,
    "cursor":         materialize_cursor,
    "icon_theme":     materialize_icon_theme,
    "kde_lockscreen": materialize_kde_lockscreen,
    # Terminals
    "kitty":     materialize_kitty,
    "alacritty": materialize_alacritty,
    "konsole":   materialize_konsole,
    # Bars
    "waybar":  materialize_waybar,
    "polybar": materialize_polybar,
    # Launchers
    "rofi": materialize_rofi,
    "wofi": materialize_wofi,
    # Notifications
    "dunst":  materialize_dunst,
    "mako":   materialize_mako,
    "swaync": materialize_swaync,
    # GNOME stack
    "gnome_shell":     materialize_gnome_shell,
    "gnome_lockscreen": materialize_gnome_lockscreen,
    # Hyprland
    "hyprland": materialize_hyprland,
    "hyprlock": materialize_hyprlock,
    # System
    "gtk":       materialize_gtk,
    "picom":     materialize_picom,
    "fastfetch": materialize_fastfetch,
    "starship":  materialize_starship,
}

__all__ = [
    "APP_MATERIALIZERS",
    "materialize_kde", "materialize_kvantum", "materialize_plasma_theme",
    "materialize_cursor", "materialize_icon_theme", "materialize_kde_lockscreen",
    "_lockscreen_lnf_for_palette",
    "materialize_kitty", "materialize_alacritty", "materialize_konsole",
    "materialize_waybar", "materialize_polybar",
    "materialize_rofi", "materialize_wofi",
    "materialize_dunst", "materialize_mako", "materialize_swaync",
    "materialize_gnome_shell", "materialize_gnome_lockscreen",
    "materialize_hyprland", "materialize_hyprlock",
    "materialize_gtk", "materialize_picom", "materialize_fastfetch",
    "materialize_starship", "_build_starship_toml",
    "materialize_wallpaper",
]
