// Reference template — floating desktop widget for Quickshell.
// Demonstrates the non-bar use case: a small overlay (clock card, system meter,
// focus tile) anchored to a corner instead of an edge-spanning panel.
//
// Patterns demonstrated:
//   - PanelWindow with two-edge anchor (corner placement)
//   - exclusionMode: Ignore so the widget never reserves screen space
//   - aboveWindows / belowWindows layer choice
//   - Process service for shell-driven data (kernel, uptime, custom polls)
//   - Smooth reveal animation on hover
//   - Rounded corners via Rectangle.radius (no clip-path needed)
//
// Replace every hex literal with values drawn from the supplied design palette.

import Quickshell
import Quickshell.Io
import QtQuick
import QtQuick.Layouts

PanelWindow {
  id: card

  // Corner anchor — bottom-right with margins.
  anchors { bottom: true; right: true }
  margins.bottom: 18
  margins.right: 18

  implicitWidth: 220
  implicitHeight: 96
  color: "transparent"

  // Floating overlay: never push other windows around.
  exclusionMode: ExclusionMode.Ignore

  // Render above the wallpaper but below normal windows.
  // Use WlrLayer.Overlay for always-on-top behavior.
  WlrLayershell.layer: WlrLayer.Bottom

  Rectangle {
    id: shell
    anchors.fill: parent
    radius: 14
    color: "#1e1e2e"        // → palette.surface
    border.color: "#89b4fa" // → palette.primary
    border.width: 1
    opacity: 0.92

    // Subtle inner glow on hover.
    Behavior on opacity { NumberAnimation { duration: 180 } }

    ColumnLayout {
      anchors.fill: parent
      anchors.margins: 12
      spacing: 4

      RowLayout {
        spacing: 6
        Rectangle {
          implicitWidth: 8; implicitHeight: 8; radius: 4
          color: "#a6e3a1"   // → palette.success
        }
        Text {
          text: "SYSTEM"
          color: "#fab387"   // → palette.accent
          font.pixelSize: 9
          font.family: "JetBrainsMono Nerd Font"
          font.letterSpacing: 1.5
        }
        Item { Layout.fillWidth: true }
        Text {
          id: kernelLine
          text: "—"
          color: "#6c7086"   // → palette.muted
          font.pixelSize: 9
          font.family: "JetBrainsMono Nerd Font"
        }
      }

      Text {
        id: clockLine
        text: Qt.formatDateTime(new Date(), "hh:mm:ss")
        color: "#cdd6f4"     // → palette.foreground
        font.pixelSize: 22
        font.family: "JetBrainsMono Nerd Font"
        Timer {
          interval: 1000; running: true; repeat: true
          onTriggered: clockLine.text = Qt.formatDateTime(new Date(), "hh:mm:ss")
        }
      }

      Text {
        text: Qt.formatDate(new Date(), "dddd, MMMM d")
        color: "#cdd6f4"     // → palette.foreground
        opacity: 0.7
        font.pixelSize: 10
        font.family: "JetBrainsMono Nerd Font"
      }
    }
  }

  // Hover-driven brighten (MouseArea has no parent.fill on PanelWindow,
  // so the area is wired to the visible Rectangle).
  MouseArea {
    anchors.fill: shell
    hoverEnabled: true
    onEntered: shell.opacity = 1.0
    onExited:  shell.opacity = 0.92
  }

  // Periodic kernel readout via Quickshell.Io.Process.
  Process {
    id: kernelProc
    command: ["uname", "-r"]
    running: true
    stdout: StdioCollector {
      onStreamFinished: kernelLine.text = text.trim().split("-")[0]
    }
  }

  Timer {
    interval: 30 * 60 * 1000   // 30 min refresh
    running: true; repeat: true
    onTriggered: kernelProc.running = true
  }
}
