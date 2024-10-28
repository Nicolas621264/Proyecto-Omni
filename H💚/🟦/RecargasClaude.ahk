#NoEnv
#SingleInstance Force
SetWorkingDir %A_ScriptDir%

; Esperar 2 segundos antes de comenzar
Sleep, 2000

; Nueva secuencia de teclas (modificación solicitada)
Send, #{t}  ; Windows + T
Sleep, 500
Send, #{0}  ; Windows + 0
Sleep, 500
Send, !{F4}  ; Alt + F4
Sleep, 1000  ; Espera un segundo adicional antes de seguir

; Secuencia de teclas original
Send, #{t}  ; Windows + T
Sleep, 500
Send, +{Tab}  ; Shift + Tab
Sleep, 500
Send, {Enter}
Sleep, 500
Send, {Tab}
Sleep, 2000
Send, {Right}
Sleep, 500
Send, {Enter}
