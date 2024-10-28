#SingleInstance Force
SetWorkingDir %A_ScriptDir%
CoordMode, Mouse, Screen
CoordMode, Pixel, Screen

; Variables globales
global isInspecting := false

; Crear GUI para mostrar información en tiempo real
Gui, InspectGUI:+AlwaysOnTop -Caption +ToolWindow
Gui, InspectGUI:Font, s10, Segoe UI
Gui, InspectGUI:Add, Text, vInfoText w300 h150, Iniciando...
Gui, InspectGUI:Color, FFFFFF

; Crear GUI para el estado
Gui, StatusGUI:+AlwaysOnTop -Caption +ToolWindow
Gui, StatusGUI:Color, 2C3E50, FFFFFF
Gui, StatusGUI:Font, s12 cWhite, Segoe UI
Gui, StatusGUI:Add, Text, vStatusText w200 Center, ESPERANDO

^!4:: ; Ctrl + Alt + 4
{
    if (!isInspecting)
    {
        ; Iniciar modo inspección
        isInspecting := true
        
        ; Mostrar GUI de estado
        Gui, StatusGUI:Show, NoActivate y0
        GuiControl, StatusGUI:, StatusText, INSPECCIONANDO
        
        ; Iniciar el timer para actualizar la información
        SetTimer, UpdateInspectInfo, 50
        
        ; Mostrar la GUI principal
        Gui, InspectGUI:Show, NoActivate w300 h150
        
        ; Mostrar mensaje inicial
        MsgBox, 64, Inspección Activada, Modo inspección activado!`n`nMueve el cursor para ver la información.`nPresiona Ctrl+Alt+4 nuevamente para capturar los datos.
    }
    else
    {
        ; Desactivar inspección
        isInspecting := false
        SetTimer, UpdateInspectInfo, Off
        
        ; Ocultar GUIs
        Gui, InspectGUI:Hide
        Gui, StatusGUI:Hide
        
        ; Capturar información final
        MouseGetPos, mouseX, mouseY, windowUnderCursor, controlUnderCursor
        WinGet, activeProcess, ProcessName, A
        WinGetTitle, activeTitle, A
        WinGetClass, activeClass, A
        PixelGetColor, pixelColor, %mouseX%, %mouseY%, RGB
        
        ; Capturar colores alrededor
        PixelGetColor, colorUp, mouseX, mouseY-1, RGB
        PixelGetColor, colorDown, mouseX, mouseY+1, RGB
        PixelGetColor, colorLeft, mouseX-1, mouseY, RGB
        PixelGetColor, colorRight, mouseX+1, mouseY, RGB
        
        ; Formatear la información
        FormatTime, currentTime,, yyyy-MM-dd HH:mm:ss
        itemInfo := "=== DATOS CAPTURADOS ===`n"
        itemInfo .= "Timestamp: " . currentTime . "`n`n"
        
        itemInfo .= "=== POSICIÓN ===`n"
        itemInfo .= "X=" . mouseX . " Y=" . mouseY . "`n`n"
        
        itemInfo .= "=== COLORES ===`n"
        itemInfo .= "Principal: " . pixelColor . "`n"
        itemInfo .= "Arriba: " . colorUp . "`n"
        itemInfo .= "Abajo: " . colorDown . "`n"
        itemInfo .= "Izquierda: " . colorLeft . "`n"
        itemInfo .= "Derecha: " . colorRight . "`n`n"
        
        itemInfo .= "=== VENTANA ===`n"
        itemInfo .= "Proceso: " . activeProcess . "`n"
        itemInfo .= "Título: " . activeTitle . "`n"
        itemInfo .= "Clase: " . activeClass
        
        ; Copiar al portapapeles
        Clipboard := itemInfo
        
        ; Mostrar mensaje de confirmación
        MsgBox, 64, Datos Capturados, Los datos han sido copiados al portapapeles!`n`nPresiona Ctrl+V para pegarlos.
    }
    return
}

UpdateInspectInfo:
{
    if (!isInspecting)
        return
        
    ; Obtener información actual
    MouseGetPos, mouseX, mouseY, windowUnderCursor, controlUnderCursor
    PixelGetColor, pixelColor, %mouseX%, %mouseY%, RGB
    WinGetTitle, activeTitle, ahk_id %windowUnderCursor%
    
    ; Crear texto para la GUI
    infoText := "=== INFORMACIÓN EN TIEMPO REAL ===`n"
    infoText .= "Posición: X=" . mouseX . " Y=" . mouseY . "`n"
    infoText .= "Color: " . pixelColor . "`n"
    infoText .= "Ventana: " . activeTitle
    
    ; Actualizar GUI
    GuiControl, InspectGUI:, InfoText, %infoText%
    
    ; Posicionar GUI cerca del cursor
    WinMove, ahk_class AutoHotkeyGUI, , mouseX + 20, mouseY + 20
    return
}

; Cerrar GUIs al salir
GuiClose:
GuiEscape:
    isInspecting := false
    SetTimer, UpdateInspectInfo, Off
    Gui, InspectGUI:Hide
    Gui, StatusGUI:Hide
return

Esc::
{
    isInspecting := false
    SetTimer, UpdateInspectInfo, Off
    Gui, InspectGUI:Hide
    Gui, StatusGUI:Hide
    ExitApp
}