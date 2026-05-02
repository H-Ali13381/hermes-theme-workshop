// Reference template — top bar for Quickshell (Hyprland / KDE Wayland).
// Read by workflow/nodes/craft/frameworks.py and injected as an exemplar in the
// craft prompt. NOT used by any materializer; treat as study material — every
// generated bar should be original and palette-driven.
//
// Patterns demonstrated:
//   - PanelWindow + WlrLayershell anchors + exclusionMode for panel coexistence
//   - Hyprland workspace service binding (Quickshell.Hyprland)
//   - Reactive clock via Timer
//   - Audio (Pipewire) volume readout via Quickshell.Services.Pipewire
//   - SystemTray on the right
//   - Hover states using MouseArea + state colors
//
// Replace every hex literal with values drawn from the supplied design palette.

import Quickshell
import Quickshell.Hyprland
import Quickshell.Services.Pipewire
import Quickshell.Services.SystemTray
import QtQuick
import QtQuick.Layouts

Scope {
  Variants {
    model: Quickshell.screens

    PanelWindow {
      id: bar
      property var modelData
      screen: modelData

      anchors { top: true; left: true; right: true }
      implicitHeight: 36

      // exclusionMode: ExclusionMode.Normal reserves space (default panel behaviour).
      // Use ExclusionMode.Ignore when coexisting with a native Plasma / waybar panel.
      exclusionMode: ExclusionMode.Normal

      color: "#1e1e2e"   // → palette.surface

      Rectangle {
        anchors.fill: parent
        color: "transparent"
        border.color: "#313244"   // → palette.muted, alpha-modulated
        border.width: 1
      }

      RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 12
        anchors.rightMargin: 12
        spacing: 10

        // ── Left: Hyprland workspaces ───────────────────────────────────────
        RowLayout {
          spacing: 4
          Repeater {
            model: Hyprland.workspaces
            delegate: Rectangle {
              required property var modelData
              implicitWidth: 26
              implicitHeight: 22
              radius: 6
              color: modelData.active ? "#89b4fa" : "#313244"   // → primary / surface
              Text {
                anchors.centerIn: parent
                text: modelData.id
                color: modelData.active ? "#1e1e2e" : "#cdd6f4"  // → background / foreground
                font.pixelSize: 11
                font.family: "JetBrainsMono Nerd Font"
              }
              MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: Hyprland.dispatch(`workspace ${modelData.id}`)
              }
            }
          }
        }

        Item { Layout.fillWidth: true }

        // ── Center: clock ───────────────────────────────────────────────────
        Text {
          id: clock
          color: "#cdd6f4"   // → foreground
          font.pixelSize: 13
          font.family: "JetBrainsMono Nerd Font"
          text: Qt.formatDateTime(new Date(), "ddd dd MMM  hh:mm")
          Timer {
            interval: 1000; running: true; repeat: true
            onTriggered: clock.text = Qt.formatDateTime(new Date(), "ddd dd MMM  hh:mm")
          }
        }

        Item { Layout.fillWidth: true }

        // ── Right: volume + system tray ─────────────────────────────────────
        RowLayout {
          spacing: 8

          // Pipewire master volume
          Text {
            color: "#fab387"   // → accent
            font.pixelSize: 12
            font.family: "JetBrainsMono Nerd Font"
            property var sink: Pipewire.defaultAudioSink
            text: sink && sink.audio
                  ? `VOL ${Math.round(sink.audio.volume * 100)}%`
                  : "VOL —"
          }

          // System tray icons
          Repeater {
            model: SystemTray.items
            delegate: Item {
              required property SystemTrayItem modelData
              implicitWidth: 18
              implicitHeight: 18
              IconImage {
                anchors.fill: parent
                source: modelData.icon
              }
              MouseArea {
                anchors.fill: parent
                acceptedButtons: Qt.LeftButton | Qt.RightButton
                onClicked: (m) => m.button === Qt.RightButton
                  ? modelData.display(bar, x, y + parent.height)
                  : modelData.activate()
              }
            }
          }
        }
      }
    }
  }
}
