#NoEnv
SendMode Input
SetWorkingDir %A_ScriptDir%

^!c::  ; Atajo: Ctrl + Alt + C
    ; Esperar 2 segundos antes de empezar
    Sleep, 2000
    Sleep, 500  ; Esperar 500 ms para asegurar que la aplicación se abra
    ; Presionar Ctrl + A para seleccionar todo el contenido
    Send, ^a
    Sleep, 500  ; Esperar 500 ms para asegurar que el contenido se seleccione
    ; Presionar Ctrl + C para copiar el contenido seleccionado
    Send, ^c
    Sleep, 500  ; Esperar para asegurar que el contenido se haya copiado
    
    ; Nuevas acciones
    Send, #1  ; Presionar Windows + 1
    Sleep, 500  ; Esperar para que la aplicación se active
    Send, ^1  ; Presionar Ctrl + 1
    Sleep, 500  ; Esperar para que la acción se complete
    Send, ^v  ; Presionar Ctrl + V para pegar
return