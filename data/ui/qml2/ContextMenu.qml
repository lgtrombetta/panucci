
import QtQuick 2.0

Item {
    id: contextMenuArea
    property variant items: []
    signal close
    signal response(int index)

    MouseArea {
        anchors.fill: parent
    }
    Rectangle {
        color: themeController.background
        anchors.fill: parent
        opacity: .9
    }
    ListView {
        model: contextMenuArea.items
        anchors.fill: parent
        header: Item { height: config.font_size * 5
                       width: parent.width
                       MouseArea { anchors.fill: parent
                                   onClicked: contextMenuArea.close()
                       }
                }
        footer: Item { height: config.font_size * 5
                       width: parent.width
                       MouseArea { anchors.fill: parent
                                   onClicked: contextMenuArea.close()
                       }
                }

        delegate: SelectableItem {
            ShadowText {
                anchors {
                    left: parent.left
                    right: parent.right
                    verticalCenter: parent.verticalCenter
                    leftMargin: config.font_size * 5
                }
                color: themeController.foreground
                font.pixelSize: config.font_size * 1.4
                text: modelData.text
            }
            onSelected: {
                contextMenuArea.close()
                modelData.trigger()
            }
        }
    }
}
