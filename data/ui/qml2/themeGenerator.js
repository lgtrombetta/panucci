
var themeButtons=new Array()

function createThemeButtons() {
    var component
    component = Qt.createComponent("SettingsButtonSmall.qml")
    var button
    // On harmattan some height get lost, increase a bit
    var ypos = theme_text.y + (config.font_size * 2.5)
    var count = 0
    var i
    for (i=0;i<themes.length;i++) {
        button = component.createObject(settingsFlick.contentItem)
        if (count == 0) {
            button.x = settingsFlick.width / 25
            button.y = ypos
            count++
            settingsFlick.contentHeight = ypos + (config.font_size * 7)
        }
        else if (count == 1) {
            button.x = (settingsFlick.width / 25 * 2) + button.width
            button.y = ypos
            count++
        }
        else if (count == 2) {
            button.x = (settingsFlick.width / 25 * 3) + (button.width * 2)
            button.y = ypos
            count++
        }
        else {
            button.x = (settingsFlick.width / 25 * 4) + (button.width * 3)
            button.y = ypos
            count = 0
            ypos = ypos + (config.font_size * 5)
        }
        button.text = themes[i].substr(0, 1).toUpperCase() + themes[i].substr(1)
        button.checked = config.theme == button.text.toLowerCase() ? true : false
        button.clicked.connect(themeButtonClicked)
        themeButtons[i] = button
    }
}
