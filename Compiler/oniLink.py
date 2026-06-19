# Compiler/oniLink.py
import subprocess, os, sys, importlib, shutil

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
LIBRARY_PATH = os.path.join(CURRENT_DIR, "..", "Library")
COMPILER_PATH = CURRENT_DIR

if LIBRARY_PATH not in sys.path:
    sys.path.insert(0, LIBRARY_PATH)
if COMPILER_PATH not in sys.path:
    sys.path.insert(0, COMPILER_PATH)

pycache_lib = os.path.join(LIBRARY_PATH, "__pycache__")
pycache_comp = os.path.join(COMPILER_PATH, "__pycache__")
for p in [pycache_lib, pycache_comp]:
    if os.path.exists(p):
        shutil.rmtree(p)

for mod in ['WinX64', 'Fluent', 'Fluent_core', 'Fluent_uix', 'FluentFuncX64', 'std', 'oniConditions', 'RegEdit', 'FluentX64', 'Win_init_x64', 'Win_proc_x64']:
    sys.modules.pop(mod, None)

import WinX64
import Fluent
import Fluent_core
import Fluent_uix
import FluentFuncX64
import std
import oniConditions
import RegEdit

importlib.reload(WinX64)
importlib.reload(Fluent)
importlib.reload(Fluent_core)
importlib.reload(Fluent_uix)
importlib.reload(FluentFuncX64)
importlib.reload(std)
importlib.reload(oniConditions)
importlib.reload(RegEdit)

USER_PROFILE = os.environ.get("USERPROFILE", "")
FASM_PATH = os.path.join(USER_PROFILE, "Desktop", "FASM", "fasm.exe") if os.path.exists(os.path.join(USER_PROFILE, "Desktop", "FASM", "fasm.exe")) else r"C:\fasm\fasm.exe"
INPUT_FILE = os.path.join("..", "main.wise") if os.path.exists(os.path.join("..", "main.wise")) else "main.wise"
ASM_FILE, EXE_FILE = "out.asm", "main.exe"

def parse_console_code(code):
    import re
    commands = []
    variables = {}
    lines = code.splitlines()
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        if not line or line.startswith("Use") or line.startswith("init") or line.startswith("reg.") or line.startswith("#"):
            i += 1
            continue
        
        m = re.match(r'run\s+(.+)', line)
        if m:
            commands.append({"type": "sys_run", "cmd": m.group(1).strip()})
            i += 1
            continue
        
        m = re.match(r'string\s+(\w+)\s*=\s*"(.*?)"', line)
        if m:
            var_name = m.group(1)
            var_value = m.group(2)
            variables[var_name] = {"type": "string", "value": var_value}
            i += 1
            continue
        
        m = re.match(r'string\s+(\w+)\s*=\s*input\("(.*?)"\)', line)
        if m:
            var_name = m.group(1)
            prompt = m.group(2)
            variables[var_name] = {"type": "input_string", "value": ""}
            commands.append({"type": "sys_input", "var": var_name, "v_type": "string", "prompt": prompt})
            i += 1
            continue
        
        m = re.match(r'int\s+(\w+)\s*=\s*input\("(.*?)"\)', line)
        if m:
            var_name = m.group(1)
            prompt = m.group(2)
            variables[var_name] = {"type": "int", "value": 0}
            commands.append({"type": "sys_input_int", "var": var_name, "prompt": prompt})
            i += 1
            continue
        
        m = re.match(r'int\s+(\w+)\s*=\s*(\d+)', line)
        if m:
            var_name = m.group(1)
            var_value = int(m.group(2))
            variables[var_name] = {"type": "int", "value": var_value}
            i += 1
            continue
        
        m = re.match(r'print\s+(.+)', line)
        if m:
            content = m.group(1).strip()
            if "+" in content:
                parts = []
                for part in content.split("+"):
                    part = part.strip()
                    if part.startswith('"') and part.endswith('"'):
                        parts.append(part.strip('"'))
                    elif part.startswith("[") and part.endswith("]"):
                        parts.append(part)
                commands.append({"type": "concat", "value": parts})
            else:
                if content.startswith('"') and content.endswith('"'):
                    commands.append({"type": "raw_string", "value": content.strip('"')})
                elif content.startswith("[") and content.endswith("]"):
                    var_name = content[1:-1]
                    commands.append({"type": "print_var", "var": var_name})
            i += 1
            continue
        
        if line.startswith("if"):
            is_cond, cond_info = oniConditions.parse_line(line, variables)
            if is_cond:
                commands.append(cond_info)
                i += 1
                continue
        
        if line.startswith("} else {"):
            commands.append({"type": "else_start"})
            i += 1
            continue
        
        if line == "}":
            commands.append({"type": "block_end"})
            i += 1
            continue
        
        if line == "pause":
            commands.append({"type": "sys_pause"})
            i += 1
            continue
        
        i += 1
    
    return commands, variables

def build_console_asm(commands, variables, code):
    reg_commands = RegEdit.parse_reg_commands(code)
    
    data_lines = ["num_fmt db '%d',0"]
    code_lines = [
        "start:",
        "    invoke SetConsoleOutputCP, 65001",
        "    invoke GetStdHandle, STD_OUTPUT_HANDLE",
        "    mov rbx, rax",
        "    invoke GetStdHandle, STD_INPUT_HANDLE",
        "    mov rsi, rax"
    ]
    
    # Добавляем данные для reg-команд
    if reg_commands:
        reg_data = RegEdit.generate_reg_data(reg_commands)
        data_lines += reg_data
    
    # Сразу выполняем reg-команды если нет условий
    if reg_commands:
        has_condition = any(cmd['type'] == 'if_start' for cmd in commands)
        if not has_condition:
            reg_code = RegEdit.generate_reg_code(reg_commands)
            code_lines += reg_code
    
    skip_until_endif = False
    last_if_idx = 0
    is_dynamic_if = False
    reg_cmd_index = 0  # Счётчик reg-команд
    
    for i, cmd in enumerate(commands):
        if cmd['type'] == 'if_start':
            last_if_idx = i
            is_dynamic_if = cmd.get('is_dynamic', False)
            if is_dynamic_if:
                skip_until_endif = False
                var_name = cmd['var']
                val = cmd['val']
                data_lines.append(f"if_const_{i} db '{val}',0")
                data_lines.append(f"if_const_len_{i} = $ - if_const_{i} - 1")
                code_lines += [
                    f"    mov rsi, var_{var_name}",
                    f"    mov rdi, if_const_{i}",
                    f"    mov rcx, [var_{var_name}_len]",
                    f"    cmp rcx, if_const_len_{i}",
                    f"    jne .else_{i}",
                    f"    repe cmpsb",
                    f"    jne .else_{i}"
                ]
                # Вставляем reg-команду по индексу внутрь if
                if reg_commands and reg_cmd_index < len(reg_commands):
                    reg_code = RegEdit.generate_reg_code([reg_commands[reg_cmd_index]], reg_cmd_index)
                    code_lines += reg_code
                    reg_cmd_index += 1
            else:
                skip_until_endif = not cmd.get('met', True)
            continue
        
        if cmd['type'] == 'else_start':
            if not is_dynamic_if and not skip_until_endif:
                code_lines.append(f"    jmp .end_if_{last_if_idx}")
            elif is_dynamic_if:
                code_lines.append(f"    jmp .end_if_{last_if_idx}")
            code_lines.append(f"  .else_{last_if_idx}:")
            if not is_dynamic_if:
                skip_until_endif = not skip_until_endif
            continue
        
        if cmd['type'] == 'block_end':
            code_lines.append(f"  .end_if_{last_if_idx}:")
            skip_until_endif = False
            is_dynamic_if = False
            continue
        
        if skip_until_endif:
            continue
        
        if cmd['type'] == 'sys_run':
            data_lines.append(f"run_cmd_{i} db '{cmd['cmd']}',0")
            code_lines += [
                f"    lea rcx, [run_cmd_{i}]",
                f"    mov rdx, 0",
                f"    call [WinExec]"
            ]
        
        elif cmd['type'] == 'raw_string':
            text = cmd['value']
            data_lines.append(f"msg_{i} db '{text}',13,10")
            data_lines.append(f"msg_{i}_len = $ - msg_{i}")
            data_lines.append(f"written_{i} dq 0")
            code_lines.append(f"    invoke WriteFile, rbx, msg_{i}, msg_{i}_len, written_{i}, 0")
        
        elif cmd['type'] == 'concat':
            data_lines.append(f"written_{i} dq 0")
            for sub_idx, part in enumerate(cmd['value']):
                if part.startswith("[") and part.endswith("]"):
                    var_name = part[1:-1]
                    code_lines.append(f"    invoke WriteFile, rbx, var_{var_name}, [var_{var_name}_len], written_{i}, 0")
                else:
                    data_lines.append(f"msg_sub_raw_{i}_{sub_idx} db '{part}',0")
                    data_lines.append(f"msg_sub_raw_{i}_{sub_idx}_len = $ - msg_sub_raw_{i}_{sub_idx} - 1")
                    code_lines.append(f"    invoke WriteFile, rbx, msg_sub_raw_{i}_{sub_idx}, msg_sub_raw_{i}_{sub_idx}_len, written_{i}, 0")
            data_lines.append(f"crlf_{i} db 13,10")
            code_lines.append(f"    invoke WriteFile, rbx, crlf_{i}, 2, written_{i}, 0")
        
        elif cmd['type'] == 'print_var':
            var_name = cmd['var']
            var_info = variables.get(var_name, {})
            if var_info.get('type') == 'input_string':
                data_lines.append(f"written_{i} dq 0")
                data_lines.append(f"crlf_{i} db 13,10")
                code_lines += [
                    f"    invoke WriteFile, rbx, var_{var_name}, [var_{var_name}_len], written_{i}, 0",
                    f"    invoke WriteFile, rbx, crlf_{i}, 2, written_{i}, 0"
                ]
            else:
                text = var_info.get('value', '')
                data_lines.append(f"var_{i} db '{text}',13,10")
                data_lines.append(f"var_{i}_len = $ - var_{i}")
                data_lines.append(f"written_{i} dq 0")
                code_lines.append(f"    invoke WriteFile, rbx, var_{i}, var_{i}_len, written_{i}, 0")
        
        elif cmd['type'] == 'sys_input':
            var_name = cmd['var']
            prompt = cmd.get('prompt', '')
            data_lines.append(f"prompt_{var_name} db '{prompt}',0")
            data_lines.append(f"prompt_{var_name}_len = $ - prompt_{var_name} - 1")
            data_lines.append(f"var_{var_name} db 256 dup (0)")
            data_lines.append(f"var_{var_name}_len dq 0")
            data_lines.append(f"read_{var_name} dq 0")
            code_lines += [
                f"    invoke WriteFile, rbx, prompt_{var_name}, prompt_{var_name}_len, read_{var_name}, 0",
                f"    invoke ReadConsoleA, rsi, var_{var_name}, 255, read_{var_name}, 0",
                f"    mov rcx, [read_{var_name}]",
                f"    sub rcx, 2",
                f"    mov [var_{var_name}_len], rcx",
                f"    mov byte [var_{var_name} + rcx], 0"
            ]
        
        elif cmd['type'] == 'sys_input_int':
            var_name = cmd['var']
            prompt = cmd.get('prompt', '')
            data_lines.append(f"prompt_{var_name} db '{prompt}',0")
            data_lines.append(f"prompt_{var_name}_len = $ - prompt_{var_name} - 1")
            data_lines.append(f"buf_{var_name} db 64 dup (0)")
            data_lines.append(f"var_{var_name} dq 0")
            data_lines.append(f"read_{var_name} dq 0")
            code_lines += [
                f"    invoke WriteFile, rbx, prompt_{var_name}, prompt_{var_name}_len, read_{var_name}, 0",
                f"    invoke ReadConsoleA, rsi, buf_{var_name}, 63, read_{var_name}, 0",
                f"    mov rcx, [read_{var_name}]",
                f"    sub rcx, 2",
                f"    mov byte [buf_{var_name} + rcx], 0",
                f"    sub rsp, 40",
                f"    lea rcx, [buf_{var_name}]",
                f"    lea rdx, [num_fmt]",
                f"    lea r8, [var_{var_name}]",
                f"    call [crt_sscanf]",
                f"    add rsp, 40"
            ]
        
        elif cmd['type'] == 'sys_pause':
            data_lines.append(f"pause_msg_{i} db 'Press any key to continue...',0")
            data_lines.append(f"pause_msg_{i}_len = $ - pause_msg_{i} - 1")
            data_lines.append(f"pause_read_{i} dq 0")
            code_lines += [
                f"    invoke WriteFile, rbx, pause_msg_{i}, pause_msg_{i}_len, pause_read_{i}, 0",
                f"    invoke GetStdHandle, STD_INPUT_HANDLE",
                f"    mov rsi, rax",
                f"    invoke ReadConsoleA, rsi, pause_read_{i}, 1, pause_read_{i}, 0"
            ]
    
    code_lines.append("    invoke ExitProcess, 0")
    
    # Собираем секцию импортов
    libs = "kernel32, 'KERNEL32.DLL', msvcrt, 'msvcrt.dll'"
    funcs = "import kernel32, GetStdHandle, 'GetStdHandle', WriteFile, 'WriteFile', ReadConsoleA, 'ReadConsoleA', SetConsoleOutputCP, 'SetConsoleOutputCP', ExitProcess, 'ExitProcess', WaitForSingleObject, 'WaitForSingleObject', CloseHandle, 'CloseHandle'\nimport msvcrt, crt_sscanf, 'sscanf', crt_sprintf, 'sprintf', crt_strlen, 'strlen', crt_system, 'system'"
    
    # Добавляем advapi32 и user32 если есть reg команды
    if reg_commands:
        libs += ", advapi32, 'ADVAPI32.DLL', user32, 'USER32.DLL'"
        funcs += "\nimport advapi32, RegOpenKeyExA, 'RegOpenKeyExA', RegSetValueExA, 'RegSetValueExA', RegCloseKey, 'RegCloseKey'\nimport user32, SendMessageTimeoutA, 'SendMessageTimeoutA'"
    
    # Добавляем shell32 только если есть sys_run
    has_run = any(cmd['type'] == 'sys_run' for cmd in commands)
    if has_run:
        libs += ", shell32, 'shell32.dll'"
        funcs += "\nimport shell32, ShellExecuteExA, 'ShellExecuteExA'"
    
    return f"""format PE64 CONSOLE
entry start
include 'win64a.inc'
section '.data' data readable writeable
{chr(10).join(data_lines)}
section '.code' code readable executable
{chr(10).join(code_lines)}
section '.idata' import data readable writeable
library {libs}
{funcs}
"""

def build():
    if not os.path.exists(INPUT_FILE):
        print(f" [ERROR] File {INPUT_FILE} not found!")
        return
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        code = f.read()

    if "Use WinX64" in code:
        asm_content = WinX64.build(code)
    elif "Use ConsoleX64" in code:
        commands, variables = parse_console_code(code)
        asm_content = build_console_asm(commands, variables, code)
    else:
        asm_content = ""

    with open(ASM_FILE, "w", encoding="utf-8") as f:
        f.write(asm_content)

    if os.path.exists(EXE_FILE):
        try:
            os.remove(EXE_FILE)
        except:
            pass

    subprocess.run(["taskkill", "/f", "/im", "main.exe"], capture_output=True)
    result = subprocess.run([FASM_PATH, ASM_FILE, EXE_FILE], capture_output=True)
    if result.returncode == 0:
        print(" [SUCCESS] Compiled!")
    else:
        print(" [FASM ERROR]\n", result.stderr.decode('cp866', errors='ignore'))

if __name__ == "__main__":
    build()