#NoEnv
#SingleInstance Force
SetWorkingDir %A_ScriptDir%

; Coordenadas específicas (esquina superior izquierda)
targetX := 1830
targetY := 892

; Función para mover la ventana
MoveDexWindow:
    WinGet, activeWindow, ID, A
    WinMove, ahk_id %activeWindow%,, %targetX%, %targetY%
    WinSet, AlwaysOnTop, On, ahk_id %activeWindow%
    WinSet, Top,, ahk_id %activeWindow%
return

; Ejecutar la función una vez al iniciar el script
SetTimer, MoveDexWindow, -1

; Salir del script
Esc::ExitApp



