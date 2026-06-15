format PE64 CONSOLE
entry start
include 'win64a.inc'
section '.data' data readable writeable
var_lang db 'WiseL',0
var_lang_len = $ - var_lang - 1
var_a dq 15
var_b dq 5
prompt_user_name db 'Введите ваше имя: ',0
prompt_user_name_len = $ - prompt_user_name - 1
var_user_name db 256 dup (0)
var_user_name_len dq 0
read_user_name dq 0
written_0 dq 0
msg_0 db '=== ТЕСТ: [print] & [math] ===',13,10
msg_0_len = $ - msg_0
written_1 dq 0
msg_sub_1_lang_0 db 'WiseL',0
msg_sub_1_lang_0_len = $ - msg_sub_1_lang_0 - 1
msg_sub_raw_1_1 db ' Compiler is fully working!',0
msg_sub_raw_1_1_len = $ - msg_sub_raw_1_1 - 1
crlf_1 db 13,10
written_2 dq 0
msg_2 db 'Результат сложения 15 + 5:',13,10
msg_2_len = $ - msg_2
written_3 dq 0
msg_3 db '20',13,10
msg_3_len = $ - msg_3
written_4 dq 0
msg_4 db '=== ТЕСТ: [input] ===',13,10
msg_4_len = $ - msg_4
written_6 dq 0
msg_sub_raw_6_0 db 'Привет, ',0
msg_sub_raw_6_0_len = $ - msg_sub_raw_6_0 - 1
msg_sub_raw_6_2 db '!',0
msg_sub_raw_6_2_len = $ - msg_sub_raw_6_2 - 1
crlf_6 db 13,10
written_7 dq 0
msg_7 db '=== ТЕСТ: [if / else] ===',13,10
msg_7_len = $ - msg_7
if_const_0 db 'Denis',0
if_const_len_0 = $ - if_const_0 - 1
written_9 dq 0
msg_9 db 'Доступ разрешен. Приветствую, Создатель! :)',13,10
msg_9_len = $ - msg_9
written_11 dq 0
msg_sub_raw_11_0 db 'Доступ открыт в режиме гостя для: ',0
msg_sub_raw_11_0_len = $ - msg_sub_raw_11_0 - 1
crlf_11 db 13,10
written_13 dq 0
msg_13 db '=== ТЕСТ: [system] ===',13,10
msg_13_len = $ - msg_13
cmd_pause_14 db 'pause',0
section '.code' code readable executable
start:
    invoke SetConsoleOutputCP, 65001
    invoke GetStdHandle, STD_OUTPUT_HANDLE
    mov rbx, rax
    invoke GetStdHandle, STD_INPUT_HANDLE
    mov rsi, rax
    invoke WriteFile, rbx, msg_0, msg_0_len, written_0, 0
    invoke WriteFile, rbx, msg_sub_1_lang_0, msg_sub_1_lang_0_len, written_1, 0
    invoke WriteFile, rbx, msg_sub_raw_1_1, msg_sub_raw_1_1_len, written_1, 0
    invoke WriteFile, rbx, crlf_1, 2, written_1, 0
    invoke WriteFile, rbx, msg_2, msg_2_len, written_2, 0
    invoke WriteFile, rbx, msg_3, msg_3_len, written_3, 0
    invoke WriteFile, rbx, msg_4, msg_4_len, written_4, 0
    invoke WriteFile, rbx, prompt_user_name, prompt_user_name_len, read_user_name, 0
    invoke ReadConsoleA, rsi, var_user_name, 255, read_user_name, 0
    mov rcx, [read_user_name]
    sub rcx, 2
    mov [var_user_name_len], rcx
    mov byte [var_user_name + rcx], 0
    invoke WriteFile, rbx, msg_sub_raw_6_0, msg_sub_raw_6_0_len, written_6, 0
    invoke WriteFile, rbx, var_user_name, [var_user_name_len], written_6, 0
    invoke WriteFile, rbx, msg_sub_raw_6_2, msg_sub_raw_6_2_len, written_6, 0
    invoke WriteFile, rbx, crlf_6, 2, written_6, 0
    invoke WriteFile, rbx, msg_7, msg_7_len, written_7, 0
    mov rsi, var_user_name
    mov rdi, if_const_0
    mov rcx, [var_user_name_len]
    cmp rcx, if_const_len_0
    jne .else_0
    repe cmpsb
    jne .else_0
    invoke WriteFile, rbx, msg_9, msg_9_len, written_9, 0
    jmp .end_if_0
.else_0:
    invoke WriteFile, rbx, msg_sub_raw_11_0, msg_sub_raw_11_0_len, written_11, 0
    invoke WriteFile, rbx, var_user_name, [var_user_name_len], written_11, 0
    invoke WriteFile, rbx, crlf_11, 2, written_11, 0
.end_if_0:
    invoke WriteFile, rbx, msg_13, msg_13_len, written_13, 0
    sub rsp, 40
    lea rcx, [cmd_pause_14]
    call [crt_system]
    add rsp, 40
    invoke ExitProcess, 0
section '.idata' import data readable writeable
library kernel32, 'KERNEL32.DLL', \
        msvcrt, 'MSVCRT.DLL'

import kernel32, \
    GetStdHandle, 'GetStdHandle', \
    WriteFile, 'WriteFile', \
    ReadConsoleA, 'ReadConsoleA', \
    SetConsoleOutputCP, 'SetConsoleOutputCP', \
    ExitProcess, 'ExitProcess'

import msvcrt, \
    crt_system, 'system'
