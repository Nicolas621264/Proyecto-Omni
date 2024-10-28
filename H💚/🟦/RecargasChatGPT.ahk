#NoEnv
#SingleInstance Force
SetWorkingDir %A_ScriptDir%

; Obtener el contador de ejecución del parámetro de línea de comandos
executionCount := A_Args[1]

; Si no se pasó ningún argumento, establecer por defecto a 1
if (executionCount == "") {
    executionCount := 1
}

; Convertir a entero
executionCount := executionCount + 0

; Esperar 2 segundos antes de comenzar
Sleep, 2000

; Nueva secuencia de teclas
Send, #{t}  ; Windows + T
Sleep, 500
Send, #{0}  ; Windows + 0
Sleep, 500
Send, !{F4}  ; Alt + F4
Sleep, 1000  ; Espera un segundo adicional

; Secuencia de teclas original
Send, #{t}  ; Windows + T
Sleep, 500
Send, +{Tab}  ; Shift + Tab
Sleep, 500
Send, {Enter}
Sleep, 500
Send, {Tab}
Sleep, 500
Send, {Enter}
Sleep, 500

; Lógica del contador para flechas a la derecha y Enter
if (executionCount == 1) {
    Send, {Enter}
} else {
    Loop, % executionCount - 1 {
        Send, {Right}
        Sleep, 100  ; Pequeña pausa entre cada flecha
    }
    Send, {Enter}
}

ExitApp