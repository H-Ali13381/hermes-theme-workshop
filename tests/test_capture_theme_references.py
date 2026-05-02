import importlib.util
import sys
import unittest
from pathlib import Path

_SCRIPTS = Path(__file__).parent.parent / "scripts"
SCRIPT_PATH = _SCRIPTS / "capture_theme_references.py"
REFERENCE_WINDOW_SCRIPT = _SCRIPTS / "reference_capture_window.py"

# Scripts are designed to run with scripts/ as the import root (ricer.py
# bootstrap prepends it). Tests that load these as standalone modules must
# replicate that, otherwise their internal `from capture_constants ...` /
# `from core.X ...` imports fail.
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))


def load_module():
    spec = importlib.util.spec_from_file_location('capture_theme_references', SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CaptureThemeReferencesTests(unittest.TestCase):
    def test_kde_baseline_contains_icons_and_core_defaults(self):
        mod = load_module()
        baseline = mod.KDE_CAPTURE_BASELINE
        self.assertEqual(baseline['colorscheme'], 'BreezeDark')
        self.assertEqual(baseline['look_and_feel'], 'org.kde.breezedark.desktop')
        self.assertEqual(baseline['plasma_theme'], 'default')
        self.assertEqual(baseline['cursor_theme'], 'breeze_cursors')
        self.assertEqual(baseline['icon_theme'], 'breeze-dark')
        self.assertEqual(baseline['widget_style'], 'Breeze')
        self.assertEqual(baseline['wallpaper'], '/usr/share/wallpapers/Next/contents/images_dark/5120x2880.png')
        self.assertEqual(baseline['capture_output'], 'DP-1')

    def test_kvantum_catalog_path_is_category_option_preview(self):
        mod = load_module()
        path = mod.catalog_preview_path('kvantum', 'catppuccin-mocha-teal')
        self.assertEqual(
            path,
            mod.CATALOG_DIR / "kvantum" / "catppuccin-mocha-teal" / "preview.png",
        )

    def test_cursor_catalog_path_is_category_option_preview(self):
        mod = load_module()
        path = mod.catalog_preview_path('cursors', 'catppuccin-macchiato-teal-cursors')
        self.assertEqual(
            path,
            mod.CATALOG_DIR / "cursors" / "catppuccin-macchiato-teal-cursors" / "preview.png",
        )

    def test_option_slug_keeps_expected_theme_name(self):
        mod = load_module()
        self.assertEqual(mod.option_slug('catppuccin-mocha-teal'), 'catppuccin-mocha-teal')
        self.assertEqual(mod.option_slug('KvArcDark'), 'kvarcdark')

    def test_category_capture_mode_uses_fullscreen(self):
        mod = load_module()
        self.assertEqual(mod.category_capture_mode('kvantum'), ('fullscreen', False))
        self.assertEqual(mod.category_capture_mode('cursors'), ('fullscreen', True))

    def test_spectacle_command_supports_activewindow_capture(self):
        mod = load_module()
        cmd = mod.build_spectacle_command(Path('/tmp/out.png'), mode='activewindow', include_pointer=False)
        self.assertIn('--activewindow', cmd)
        self.assertNotIn('--fullscreen', cmd)
        output_index = cmd.index('--output')
        self.assertEqual(cmd[output_index + 1], '/tmp/out.png')

    def test_reference_window_command_targets_helper_script(self):
        mod = load_module()
        cmd = mod.build_reference_window_command('kvantum', 'catppuccin-mocha-teal')
        self.assertEqual(cmd[0], 'python3')
        self.assertEqual(Path(cmd[1]), REFERENCE_WINDOW_SCRIPT)
        self.assertIn('--category', cmd)
        self.assertIn('kvantum', cmd)
        self.assertIn('--theme-name', cmd)
        self.assertIn('catppuccin-mocha-teal', cmd)

    def test_reference_panel_launchers_use_explicit_common_apps(self):
        mod = load_module()
        launchers = mod.REFERENCE_PANEL_LAUNCHERS
        self.assertIn('applications:firefox.desktop', launchers)
        self.assertIn('applications:org.kde.dolphin.desktop', launchers)
        self.assertIn('applications:systemsettings.desktop', launchers)
        self.assertIn('applications:org.kde.discover.desktop', launchers)
        self.assertIn('applications:org.kde.konsole.desktop', launchers)
        self.assertNotIn('preferred://browser', launchers)
        self.assertNotIn('preferred://filemanager', launchers)

    def test_scene_notes_mentions_standardized_panel_and_desktop(self):
        mod = load_module()
        self.assertIn('Breeze cursor and Breeze dark icons', mod.SCENE_NOTES)
        self.assertIn('basic KDE PC', mod.reference_scene_notes_text())
        self.assertIn('showcase standard app icons', mod.reference_scene_notes_text())

    def test_basic_scene_lists_explicit_panel_apps_and_desktop_items(self):
        mod = load_module()
        self.assertIn('Firefox', mod.REFERENCE_PANEL_APPS)
        self.assertIn('Dolphin', mod.REFERENCE_PANEL_APPS)
        self.assertIn('System Settings', mod.REFERENCE_PANEL_APPS)
        self.assertIn('Discover', mod.REFERENCE_PANEL_APPS)
        self.assertIn('Konsole', mod.REFERENCE_PANEL_APPS)
        self.assertIn('Home.desktop', mod.REFERENCE_DESKTOP_ITEMS)
        self.assertIn('Trash.desktop', mod.REFERENCE_DESKTOP_ITEMS)
        self.assertIn('Firefox.desktop', mod.REFERENCE_DESKTOP_ITEMS)
        self.assertIn('Dolphin.desktop', mod.REFERENCE_DESKTOP_ITEMS)
        self.assertIn('System Settings.desktop', mod.REFERENCE_DESKTOP_ITEMS)
        self.assertIn('Discover.desktop', mod.REFERENCE_DESKTOP_ITEMS)

    def test_reference_shortcut_specs_include_real_icons(self):
        mod = load_module()
        self.assertEqual(mod.REFERENCE_DESKTOP_SHORTCUTS['Home.desktop']['Icon'], 'user-home')
        self.assertEqual(mod.REFERENCE_DESKTOP_SHORTCUTS['Trash.desktop']['Icon'], 'user-trash')
        self.assertEqual(mod.REFERENCE_DESKTOP_SHORTCUTS['Firefox.desktop']['Icon'], 'firefox')
        self.assertEqual(mod.REFERENCE_DESKTOP_SHORTCUTS['Dolphin.desktop']['Icon'], 'system-file-manager')

    def test_desktop_shortcut_path_points_to_desktop(self):
        mod = load_module()
        path = mod.desktop_shortcut_path('Firefox.desktop')
        self.assertEqual(path, Path.home() / "Desktop" / "Firefox.desktop")

    def test_desktop_shortcut_text_has_desktop_entry_header(self):
        mod = load_module()
        text = mod.desktop_shortcut_text('Firefox.desktop', mod.REFERENCE_DESKTOP_SHORTCUTS['Firefox.desktop'])
        self.assertIn('[Desktop Entry]', text)
        self.assertIn('Name=Firefox', text)
        self.assertIn('Icon=firefox', text)
        self.assertIn('Type=Application', text)

    def test_home_shortcut_uses_link_type(self):
        mod = load_module()
        text = mod.desktop_shortcut_text('Home.desktop', mod.REFERENCE_DESKTOP_SHORTCUTS['Home.desktop'])
        self.assertIn('Type=Link', text)
        self.assertIn(f'URL=file://{Path.home()}', text)

    def test_trash_shortcut_uses_trash_url(self):
        mod = load_module()
        text = mod.desktop_shortcut_text('Trash.desktop', mod.REFERENCE_DESKTOP_SHORTCUTS['Trash.desktop'])
        self.assertIn('URL=trash:/', text)
        self.assertIn('Icon=user-trash', text)

    def test_panel_scene_summary_mentions_explicit_apps(self):
        mod = load_module()
        summary = mod.panel_scene_summary()
        self.assertIn('Firefox', summary)
        self.assertIn('Dolphin', summary)
        self.assertIn('System Settings', summary)
        self.assertIn('Discover', summary)
        self.assertIn('Konsole', summary)

    def test_scene_payload_contains_desktop_shortcuts(self):
        mod = load_module()
        payload = mod.desktop_and_panel_state_payload()
        self.assertIn('desktop_shortcuts', payload)
        self.assertIn('Firefox.desktop', payload['desktop_shortcuts'])
        self.assertIn('Home.desktop', payload['desktop_shortcuts'])

    def test_standard_scene_summary_mentions_panel_and_desktop(self):
        mod = load_module()
        summary = mod.standard_scene_human_summary()
        self.assertIn('Panel apps:', summary)
        self.assertIn('Desktop items:', summary)
        self.assertIn('Firefox', summary)
        self.assertIn('Dolphin', summary)
        self.assertIn('Home.desktop', summary)
        self.assertIn('Trash.desktop', summary)

    def test_standard_scene_human_summary_not_using_generic_labels(self):
        mod = load_module()
        self.assertNotIn('Web Browser', mod.standard_scene_human_summary())
        self.assertNotIn('File Manager', mod.standard_scene_human_summary())

    def test_reference_panel_apps_not_generic(self):
        mod = load_module()
        self.assertNotIn('Web Browser', mod.REFERENCE_PANEL_APPS)
        self.assertNotIn('File Manager', mod.REFERENCE_PANEL_APPS)

    def test_reference_panel_launchers_string_contains_five_apps(self):
        mod = load_module()
        self.assertEqual(len(mod.REFERENCE_PANEL_LAUNCHERS.split(',')), 5)

    def test_desktop_items_count_is_six(self):
        mod = load_module()
        self.assertEqual(len(mod.REFERENCE_DESKTOP_ITEMS), 6)

    def test_reference_panel_launchers_order_starts_with_firefox_and_dolphin(self):
        mod = load_module()
        self.assertTrue(mod.REFERENCE_PANEL_LAUNCHERS.startswith('applications:firefox.desktop,applications:org.kde.dolphin.desktop'))

    def test_scene_shortcuts_include_system_settings_and_discover(self):
        mod = load_module()
        self.assertIn('System Settings.desktop', mod.REFERENCE_DESKTOP_ITEMS)
        self.assertIn('Discover.desktop', mod.REFERENCE_DESKTOP_ITEMS)

    def test_reference_shortcuts_have_exec_or_url(self):
        mod = load_module()
        for spec in mod.REFERENCE_DESKTOP_SHORTCUTS.values():
            self.assertTrue('Exec' in spec or 'URL' in spec)

    def test_reference_shortcuts_all_have_names_and_icons(self):
        mod = load_module()
        for spec in mod.REFERENCE_DESKTOP_SHORTCUTS.values():
            self.assertIn('Name', spec)
            self.assertIn('Icon', spec)

    def test_standard_scene_readme_mentions_real_entries(self):
        mod = load_module()
        text = mod.standard_scene_readme_text()
        self.assertIn('Firefox.desktop', text)
        self.assertIn('Dolphin.desktop', text)
        self.assertIn('Home.desktop', text)
        self.assertIn('Trash.desktop', text)
        self.assertIn('System Settings.desktop', text)
        self.assertIn('Discover.desktop', text)

    def test_scene_metadata_payload_contains_shortcuts_and_summary(self):
        mod = load_module()
        payload = mod.scene_metadata_payload('kvantum')
        self.assertEqual(payload['category'], 'kvantum')
        self.assertIn('desktop_shortcuts', payload)
        self.assertIn('panel_apps', payload)
        self.assertIn('summary', payload)

    def test_capture_notes_describe_standardized_reference_window(self):
        mod = load_module()
        notes = mod.real_capture_notes('kvantum')
        self.assertIn('standardized reference window', notes)
        self.assertIn('fullscreen', notes)
        self.assertIn('DP-1', notes)


if __name__ == '__main__':
    unittest.main()
