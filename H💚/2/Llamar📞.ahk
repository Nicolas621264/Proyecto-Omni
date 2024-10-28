#NoEnv
#SingleInstance Force
SetWorkingDir %A_ScriptDir%
SetBatchLines -1

; Wait 2 seconds before starting
Sleep, 2000

; Sequence of keystrokes
Send, #{t}
Sleep, 500
Send, #{2}
Sleep, 500
Send, ^2
Sleep, 500
Loop, 6 {
    Send, +{Tab}
    Sleep, 100
}
Send, {Enter}