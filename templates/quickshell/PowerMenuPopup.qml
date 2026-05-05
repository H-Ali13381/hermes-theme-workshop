// Quickshell power menu scaffold for generated dashboards.
// The power glyph toggles this menu. It must not call KRunner search.
// Destructive actions use a confirm step before command execution.
import QtQuick
import QtQuick.Layouts
import Quickshell

PopupWindow {
    id: powerMenu

    required property var anchorWindow
    property bool confirmDanger: false
    property string pendingLabel: ""
    property var pendingCommand: []

    anchor.window: anchorWindow
    width: 240
    height: confirmDanger ? 150 : 244
    visible: false
    grabFocus: true

    function requestDanger(label, command) {
        pendingLabel = label
        pendingCommand = command
        confirmDanger = true
    }

    function runPending() {
        if (pendingCommand.length > 0) {
            Quickshell.execDetached(pendingCommand)
        }
        pendingCommand = []
        pendingLabel = ""
        confirmDanger = false
        visible = false
    }

    Rectangle {
        anchors.fill: parent
        radius: 14
        color: "#120f22"
        border.color: "#ffd75e"
        border.width: 2

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 12
            spacing: 8

            Loader {
                Layout.fillWidth: true
                Layout.fillHeight: true
                sourceComponent: powerMenu.confirmDanger ? confirmPane : actionPane
            }
        }
    }

    Component {
        id: actionPane
        ColumnLayout {
            spacing: 8
            GameButton { Layout.fillWidth: true; label: "Lock"; onClicked: { Quickshell.execDetached(["loginctl", "lock-session"]); powerMenu.visible = false } }
            GameButton { Layout.fillWidth: true; label: "Suspend"; onClicked: powerMenu.requestDanger("Suspend", ["systemctl", "suspend"]) }
            GameButton { Layout.fillWidth: true; label: "Reboot"; dangerous: true; onClicked: powerMenu.requestDanger("Reboot", ["systemctl", "reboot"]) }
            GameButton { Layout.fillWidth: true; label: "Power Off"; dangerous: true; onClicked: powerMenu.requestDanger("Power Off", ["systemctl", "poweroff"]) }
        }
    }

    Component {
        id: confirmPane
        ColumnLayout {
            spacing: 10
            Text {
                Layout.fillWidth: true
                text: "Confirm " + powerMenu.pendingLabel + "?"
                color: "#fff2a8"
                horizontalAlignment: Text.AlignHCenter
                font.bold: true
            }
            RowLayout {
                Layout.fillWidth: true
                GameButton { Layout.fillWidth: true; label: "Cancel"; onClicked: { powerMenu.confirmDanger = false; powerMenu.pendingCommand = [] } }
                GameButton { Layout.fillWidth: true; label: "Confirm"; dangerous: true; onClicked: powerMenu.runPending() }
            }
        }
    }
}
