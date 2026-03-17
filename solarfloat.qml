import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Window 2.15

Window {
    id: mainWindow

    readonly property color base3: "#fdf6e3"
    readonly property color base2: "#eee8d5"
    readonly property color base1: "#93a1a1"
    readonly property color base01: "#586e75"
    readonly property color blue: "#268bd2"
    property int currentFontSize: 24

    visible: true
    width: 900
    height: 600
    flags: Qt.FramelessWindowHint | Qt.Window
    color: base3 // Используем основной цвет фона
    Component.onCompleted: {
        var args = Qt.application.arguments;
        if (args.length >= 3)
            editor.text = args[args.length - 1];

    }

    Row {
        anchors.fill: parent

        // 1. ПАНЕЛЬ ПЕРЕТАСКИВАНИЯ
        Rectangle {
            id: dragHandle

            width: 40
            height: parent.height
            color: base2 // Цвет панели чуть темнее фона

            Column {
                anchors.centerIn: parent
                spacing: 8

                Repeater {
                    model: 12

                    Rectangle {
                        width: 4
                        height: 4
                        radius: 2
                        color: base1
                    }

                }

            }

            MouseArea {
                anchors.fill: parent
                cursorShape: Qt.SizeAllCursor
                onPressed: mainWindow.startSystemMove()
            }

        }

        // 2. КОНТЕЙНЕР РЕДАКТОРА
        Rectangle {
            id: editorContainer

            width: parent.width - dragHandle.width
            height: parent.height
            color: "transparent"

            ScrollView {
                id: scrollView

                anchors.fill: parent
                anchors.margins: 25
                clip: true
                // ОТКЛЮЧАЕМ ГОРИЗОНТАЛЬНЫЙ СКРОЛЛБАР
                ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

                TextEdit {
                    id: editor

                    width: scrollView.availableWidth
                    height: Math.max(contentHeight, scrollView.availableHeight)
                    focus: true
                    selectByMouse: true
                    wrapMode: TextEdit.Wrap
                    font.family: "Fira Code"
                    font.pixelSize: currentFontSize
                    font.weight: Font.DemiBold
                    color: base01 // Правильный цвет текста
                    selectionColor: blue
                    selectedTextColor: base3

                    WheelHandler {
                        acceptedModifiers: Qt.ControlModifier
                        onWheel: (event) => {
                            if (event.angleDelta.y > 0 && currentFontSize < 70)
                                currentFontSize += 2;
                            else if (event.angleDelta.y < 0 && currentFontSize > 6)
                                currentFontSize -= 2;
                        }
                    }

                }

            }

        }

    }

    // Горячие клавиши
    Shortcut {
        sequence: "Escape"
        onActivated: Qt.quit()
    }

    Shortcut {
        sequences: ["Ctrl+Plus", "Ctrl+="]
        onActivated: {
            if (currentFontSize < 70)
                currentFontSize += 2;

        }
    }

    Shortcut {
        sequence: "Ctrl+-"
        onActivated: {
            if (currentFontSize > 6)
                currentFontSize -= 2;

        }
    }

    Shortcut {
        sequence: "Ctrl+0"
        onActivated: currentFontSize = 16
    }

}
