import Qt 4.7

Item {
    id: rootWindow
    property bool showStatusBar: false
    property variant root: mainObject
    width: config.main_width
    height: config.main_height

    Main {
        id: mainObject
        anchors.fill: parent
    }
}
