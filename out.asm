format PE64 CONSOLE
entry start
include 'win64a.inc'
section '.data' data readable writeable
num_fmt db '%d',0
var_0 db '10',13,10
var_0_len = $ - var_0
written_0 dq 0
var_1 db '20',13,10
var_1_len = $ - var_1
written_1 dq 0
pause_msg_2 db 'Press any key to continue...',0
pause_msg_2_len = $ - pause_msg_2 - 1
pause_read_2 dq 0
section '.code' code readable executable
start:
    invoke SetConsoleOutputCP, 65001
    invoke GetStdHandle, STD_OUTPUT_HANDLE
    mov rbx, rax
    invoke GetStdHandle, STD_INPUT_HANDLE
    mov rsi, rax
    invoke WriteFile, rbx, var_0, var_0_len, written_0, 0
    invoke WriteFile, rbx, var_1, var_1_len, written_1, 0
    invoke WriteFile, rbx, pause_msg_2, pause_msg_2_len, pause_read_2, 0
    invoke GetStdHandle, STD_INPUT_HANDLE
    mov rsi, rax
    invoke ReadConsoleA, rsi, pause_read_2, 1, pause_read_2, 0
    invoke ExitProcess, 0
section '.idata' import data readable writeable
library kernel32, 'KERNEL32.DLL', msvcrt, 'msvcrt.dll'
import kernel32, GetStdHandle, 'GetStdHandle', WriteFile, 'WriteFile', ReadConsoleA, 'ReadConsoleA', SetConsoleOutputCP, 'SetConsoleOutputCP', ExitProcess, 'ExitProcess', WaitForSingleObject, 'WaitForSingleObject', CloseHandle, 'CloseHandle'
import msvcrt, crt_sscanf, 'sscanf', crt_sprintf, 'sprintf', crt_strlen, 'strlen', crt_system, 'system'
