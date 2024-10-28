#NoEnv
SendMode Input
SetWorkingDir %A_ScriptDir%

; Esperar 2 segundos antes de empezar
Sleep, 2000

; Presionar Tab 5 veces
Loop, 5 {
    Send, {Tab}
    Sleep, 100  ; Pequeña pausa entre cada Tab
}

; Presionar Enter
Send, {Enter}
Sleep, 500  ; Esperar 500 ms después de presionar Enter

; Presionar Windows + 7 para abrir la tercera aplicación anclada
Send, #{7}
Sleep, 500  ; Esperar 500 ms para asegurar que la aplicación se abra

; Presionar Ctrl + A para seleccionar todo el contenido
Send, ^a
Sleep, 500  ; Esperar 500 ms para asegurarse de que el contenido se seleccione

; Presionar Ctrl + V para pegar el contenido del portapapeles
Send, ^v
