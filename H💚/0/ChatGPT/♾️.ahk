#NoEnv
#SingleInstance Force
SetWorkingDir %A_ScriptDir%  ; Configuración inicial
SetBatchLines -1  ; Mejora el rendimiento del script

; Secuencia inicial de teclas
Send, #{t}
Sleep, 500
Send, #{0}
Sleep, 500
Send, ^v
Sleep, 500
Send, {Enter}