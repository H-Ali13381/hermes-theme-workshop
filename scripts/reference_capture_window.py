#!/usr/bin/env python3
"""
Open a standardized reference window for theme capture.

This is intentionally simple and deterministic:
- one Qt window for Kvantum/widget comparisons
- one cursor reference board for cursor captures

The window stays open until killed by the caller.
"""

from __future__ import annotations

import argparse
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenuBar,
    QPushButton,
    QProgressBar,
    QRadioButton,
    QScrollBar,
    QSlider,
    QSpinBox,
    QTabWidget,
    QTextEdit,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

APP_TITLE = "Hermes Ricer Reference Window"


def build_kvantum_window(theme_name: str) -> QMainWindow:
    win = QMainWindow()
    win.setWindowTitle(f"{APP_TITLE} — Kvantum — {theme_name}")
    win.resize(1280, 860)

    menubar = QMenuBar(win)
    file_menu = menubar.addMenu("File")
    file_menu.addAction(QAction("Open", win))
    file_menu.addAction(QAction("Save", win))
    file_menu.addSeparator()
    file_menu.addAction(QAction("Quit", win))
    edit_menu = menubar.addMenu("Edit")
    edit_menu.addAction(QAction("Preferences", win))
    view_menu = menubar.addMenu("View")
    view_menu.addAction(QAction("Toggle Sidebar", win))
    win.setMenuBar(menubar)

    toolbar = QToolBar("Main Toolbar", win)
    toolbar.addAction(QAction("Run", win))
    toolbar.addAction(QAction("Build", win))
    toolbar.addAction(QAction("Deploy", win))
    win.addToolBar(toolbar)

    central = QWidget()
    layout = QVBoxLayout(central)

    header = QLabel(f"Reference Qt widget scene — {theme_name}")
    header.setStyleSheet("font-size: 22px; font-weight: 700;")
    layout.addWidget(header)

    tabs = QTabWidget()
    layout.addWidget(tabs)

    controls = QWidget()
    controls_layout = QGridLayout(controls)

    form_box = QGroupBox("Forms")
    form_layout = QGridLayout(form_box)
    form_layout.addWidget(QLabel("Project name"), 0, 0)
    form_layout.addWidget(QLineEdit("void-dragon"), 0, 1)
    form_layout.addWidget(QLabel("Theme preset"), 1, 0)
    combo = QComboBox()
    combo.addItems(["catppuccin-mocha-teal", "catppuccin-mocha-mauve", "catppuccin-mocha-peach", "catppuccin-mocha-yellow"])
    combo.setCurrentText(theme_name)
    form_layout.addWidget(combo, 1, 1)
    form_layout.addWidget(QLabel("Iterations"), 2, 0)
    form_layout.addWidget(QSpinBox(), 2, 1)
    controls_layout.addWidget(form_box, 0, 0)

    toggles_box = QGroupBox("Toggles")
    toggles_layout = QVBoxLayout(toggles_box)
    toggles_layout.addWidget(QCheckBox("Enable blur"))
    toggles_layout.addWidget(QCheckBox("Rounded corners"))
    toggles_layout.addWidget(QRadioButton("Dark mode baseline"))
    toggles_layout.addWidget(QRadioButton("Light mode baseline"))
    controls_layout.addWidget(toggles_box, 0, 1)

    actions_box = QGroupBox("Actions")
    actions_layout = QVBoxLayout(actions_box)
    row = QHBoxLayout()
    row.addWidget(QPushButton("Apply"))
    row.addWidget(QPushButton("Cancel"))
    row.addWidget(QPushButton("Preview"))
    actions_layout.addLayout(row)
    progress = QProgressBar()
    progress.setRange(0, 100)
    progress.setValue(66)
    actions_layout.addWidget(progress)
    slider = QSlider(Qt.Orientation.Horizontal)
    slider.setValue(35)
    actions_layout.addWidget(slider)
    controls_layout.addWidget(actions_box, 1, 0, 1, 2)

    tabs.addTab(controls, "Controls")

    editor = QWidget()
    editor_layout = QVBoxLayout(editor)
    editor_layout.addWidget(QLabel("Notes"))
    text = QTextEdit()
    text.setPlainText(
        "This window exists only for standardized theme capture.\n\n"
        "Look at button chrome, input borders, combo boxes, tab styling,\n"
        "checkboxes, sliders, progress bars, and menu/toolbar surfaces."
    )
    editor_layout.addWidget(text)
    tabs.addTab(editor, "Editor")

    scroll_demo = QWidget()
    scroll_layout = QHBoxLayout(scroll_demo)
    scroll_layout.addWidget(QTextEdit("Scrollable content\n" * 30))
    scroll_layout.addWidget(QScrollBar(Qt.Orientation.Vertical))
    tabs.addTab(scroll_demo, "Scroll")

    win.setCentralWidget(central)
    return win


def build_cursor_window(theme_name: str) -> QMainWindow:
    win = QMainWindow()
    win.setWindowTitle(f"{APP_TITLE} — Cursor — {theme_name}")
    win.resize(1180, 760)

    central = QWidget()
    layout = QVBoxLayout(central)
    title = QLabel(f"Cursor reference scene — {theme_name}")
    title.setStyleSheet("font-size: 22px; font-weight: 700;")
    layout.addWidget(title)

    help_text = QLabel(
        "Move the mouse across the labeled zones before capture so the active cursor shape is visible.\n"
        "This board gives contrast and edge context for the pointer."
    )
    help_text.setWordWrap(True)
    layout.addWidget(help_text)

    grid = QGridLayout()
    zones = [
        ("Normal pointer zone", "background: #1e1e2e; border: 2px solid #7ad4f0; min-height: 140px;"),
        ("Text cursor zone", "background: #26233a; border: 2px solid #c4a7e7; min-height: 140px;"),
        ("Resize edge zone", "background: #282828; border: 2px solid #d4a012; min-height: 140px;"),
        ("Link / hand zone", "background: #1a1b26; border: 2px solid #89b4fa; min-height: 140px;"),
    ]
    for i, (label_text, style) in enumerate(zones):
        label = QLabel(label_text)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(style + " font-size: 18px; font-weight: 600;")
        grid.addWidget(label, i // 2, i % 2)
    layout.addLayout(grid)

    line = QLineEdit("Editable line for I-beam cursor")
    layout.addWidget(line)

    win.setCentralWidget(central)
    return win


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Open a standardized reference capture window.")
    parser.add_argument("--category", choices=["kvantum", "cursors"], required=True)
    parser.add_argument("--theme-name", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    app = QApplication(sys.argv)
    if args.category == "kvantum":
        win = build_kvantum_window(args.theme_name)
    else:
        win = build_cursor_window(args.theme_name)
    # Find the capture target screen (DP-1) by name, fall back to primary
    target_screen = None
    for screen in app.screens():
        if "DP-1" in screen.name():
            target_screen = screen
            break
    if target_screen is None:
        target_screen = app.primaryScreen()

    win.show()
    if target_screen:
        geo = target_screen.availableGeometry()
        # Center the window on DP-1
        x = geo.x() + (geo.width() - win.width()) // 2
        y = geo.y() + (geo.height() - win.height()) // 2
        win.move(x, y)
    win.raise_()
    win.activateWindow()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
