# Library/RegEdit.py
"""Работа с реестром Windows через WinAPI x64"""
import re

HKEYS = {
    "HKEY_CLASSES_ROOT": "0x80000000",
    "HKEY_CURRENT_USER": "0x80000001",
    "HKEY_LOCAL_MACHINE": "0x80000002",
    "HKEY_USERS": "0x80000003",
    "HKEY_CURRENT_CONFIG": "0x80000005",
}

def parse_reg_commands(code):
    commands = []
    for raw in code.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r'reg\.set\s+"(.+?)\\(.+?)"\s+"(.+?)"\s*=\s*"(.+?)"', line)
        if m:
            full_path = m.group(1)
            subkey = m.group(2)
            value_name = m.group(3)
            value = m.group(4)
            root = full_path.split("\\")[0]
            rest = "\\".join(full_path.split("\\")[1:])
            full_key = rest + "\\" + subkey if rest else subkey
            hkey = HKEYS.get(root, "0x80000001")
            commands.append({
                "type": "reg_set", 
                "hkey": hkey, 
                "subkey": full_key, 
                "value_name": value_name, 
                "value": value
            })
            continue
    return commands

def generate_reg_data(commands):
    data = [
        "hKey dq 0",
        "dwResult dd 0",
        "env_string db 'Colors',0",
    ]
    for i, cmd in enumerate(commands):
        if cmd['type'] == 'reg_set':
            data.append(f"reg_subkey_{i} db '{cmd['subkey']}',0")
            data.append(f"reg_valname_{i} db '{cmd['value_name']}',0")
            data.append(f"reg_val_{i} db '{cmd['value']}',0")
            data.append(f"reg_val_{i}_len = $ - reg_val_{i}")
    return data

def generate_reg_code(commands, cmd_index=0):
    code = []
    for i, cmd in enumerate(commands):
        if cmd['type'] == 'reg_set':
            idx = cmd_index + i  # Используем правильный индекс!
            code += [
                f"    ; ========== REG SET: {cmd['subkey']}\\{cmd['value_name']} = {cmd['value']} ==========",
                f"    ; RegOpenKeyExA",
                f"    mov [hKey], 0",
                f"    sub rsp, 40",
                f"    mov rcx, {cmd['hkey']}",
                f"    lea rdx, [reg_subkey_{idx}]",
                f"    mov r8d, 0",
                f"    mov r9d, 2",
                f"    lea rax, [hKey]",
                f"    mov [rsp+32], rax",
                f"    call [RegOpenKeyExA]",
                f"    add rsp, 40",
                f"    cmp eax, 0",
                f"    jne .reg_end_{idx}",
                f"    ; RegSetValueExA",
                f"    sub rsp, 56",
                f"    mov rcx, [hKey]",
                f"    lea rdx, [reg_valname_{idx}]",
                f"    mov r8d, 0",
                f"    mov r9d, 1",
                f"    lea rax, [reg_val_{idx}]",
                f"    mov [rsp+32], rax",
                f"    mov eax, reg_val_{idx}_len",
                f"    mov [rsp+40], eax",
                f"    call [RegSetValueExA]",
                f"    add rsp, 56",
                f"    ; RegCloseKey",
                f"    sub rsp, 32",
                f"    mov rcx, [hKey]",
                f"    call [RegCloseKey]",
                f"    add rsp, 32",
                f"    ; SendMessageTimeoutA",
                f"    sub rsp, 56",
                f"    mov ecx, 0xFFFF",
                f"    mov edx, 0x001A",
                f"    xor r8d, r8d",
                f"    lea r9, [env_string]",
                f"    mov qword [rsp+32], 2",
                f"    mov qword [rsp+40], 5000",
                f"    lea rax, [dwResult]",
                f"    mov [rsp+48], rax",
                f"    call [SendMessageTimeoutA]",
                f"    add rsp, 56",
                f"  .reg_end_{idx}:",
            ]
    return code