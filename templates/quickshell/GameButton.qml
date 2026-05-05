// Reusable Quickshell button for generated RPG/dashboard widgets.
// MouseArea is anchored to the visible Rectangle so hover/pressed geometry
// matches the art. Use this instead of invisible flat MouseArea overlays.
import QtQuick

Rectangle {
    id: button

    property string label: "Button"
    property bool active: false
    property bool dangerous: false
    property int feedbackMargin: mouse.containsPress ? 4 : mouse.containsMouse ? -2 : 1
    signal clicked()

    implicitWidth: Math.max(150, labelText.implicitWidth + 36)
    implicitHeight: 42
    radius: 8

    color: mouse.containsPress ? (dangerous ? "#4b1515" : "#3b235f")
         : mouse.containsMouse ? (dangerous ? "#7b2520" : "#4c35a3")
         : active ? "#36244f"
         : "#201832"

    border.color: mouse.containsPress ? "#fff2a8"
                : mouse.containsMouse ? "#ffd75e"
                : active ? "#d09b45"
                : "#7b5cff"
    border.width: mouse.containsMouse || active ? 2 : 1
    scale: mouse.containsPress ? 0.96 : mouse.containsMouse ? 1.03 : 1.0
    opacity: enabled ? 1.0 : 0.45

    Behavior on color { ColorAnimation { duration: 90 } }
    Behavior on border.color { ColorAnimation { duration: 90 } }
    Behavior on scale { NumberAnimation { duration: 80; easing.type: Easing.OutQuad } }
    Behavior on opacity { NumberAnimation { duration: 80 } }
    Behavior on feedbackMargin { NumberAnimation { duration: 80; easing.type: Easing.OutQuad } }

    Rectangle {
        anchors.fill: parent
        anchors.margins: button.feedbackMargin
        radius: button.radius
        color: "transparent"
        border.color: mouse.containsMouse ? "#fff2a8" : "transparent"
        border.width: 1
        opacity: mouse.containsMouse ? 0.55 : 0
        Behavior on opacity { NumberAnimation { duration: 80 } }
    }

    Text {
        id: labelText
        anchors.centerIn: parent
        text: button.label
        color: mouse.containsPress ? "#fff7cf" : "#f0eaff"
        font.pixelSize: 15
        font.bold: mouse.containsMouse || active
    }

    MouseArea {
        id: mouse
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
        acceptedButtons: Qt.LeftButton
        onClicked: if (button.enabled) button.clicked()
    }
}
