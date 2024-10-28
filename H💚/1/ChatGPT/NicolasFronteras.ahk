#NoEnv
#SingleInstance Force
SetWorkingDir %A_ScriptDir%
SetBatchLines -1

; Esperar 2 segundos antes de comenzar
Sleep, 2000

; Secuencia de teclas
Send, #{t}
Sleep, 500
Send, #{1}
Sleep, 500
Send, ^1
Sleep, 500
Send, ^v
Sleep, 500
Send, {Enter}
