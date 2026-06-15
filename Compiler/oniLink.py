import re, subprocess, os
import oniConditions 

USER_PROFILE = os.environ.get("USERPROFILE", "")
FASM_PATH = os.path.join(USER_PROFILE, "Desktop", "FASM", "fasm.exe")
if not os.path.exists(FASM_PATH):
    FASM_PATH = r"C:\fasm\fasm.exe"

INPUT_FILE = "main.wise"
ASM_FILE = os.path.join("Compiler", "out.asm")
EXE_FILE = os.path.join("Compiler", "main.exe")

def parse_code(code):
    variables, commands = {}, []

    for line in code.splitlines():
        line = line.strip()
        if not line or line.startswith("Use") or line.startswith("init") or line.startswith("#"): continue

        is_cond, cond_data = oniConditions.parse_line(line, variables)
        if is_cond:
            commands.append(cond_data)
            continue

        input_match = re.match(r'string\s+(\w+)\s*=\s*input\s*\(\s*"(.*?)"\s*\)', line)
        if input_match:
            v_name, prompt = input_match.groups()
            variables[v_name] = {'type': 'input_string', 'value': prompt}
            commands.append({'type': 'sys_input', 'var': v_name, 'prompt': prompt})
            continue

        var_match = re.match(r'(string|int|boolean)\s+(\w+)\s*=\s*(.*)', line)
        if var_match:
            v_type, v_name, v_val = var_match.groups()
            v_val = v_val.strip('"') if v_type == "string" else (int(eval(v_val)) if v_type == "int" else (1 if v_val.strip() == "True" else 0))
            variables[v_name] = {'type': v_type, 'value': v_val}
            continue

        if line == 'system "pause"':
            commands.append({'type': 'sys_pause'})
            continue

        if line.startswith("print"):
            content = line[5:].strip()
            if content.startswith("[") and content.endswith("]"): commands.append({'type': 'expr', 'value': content[1:-1].strip()})
            elif "+" in content and "[" in content: commands.append({'type': 'concat', 'value': [p.strip() for p in content.split("+")]})
            elif content.startswith('"') and content.endswith('"'): commands.append({'type': 'raw_string', 'value': content.strip('"')})

    return variables, commands

def generate_fasm(variables, commands):
    data, code = [], []
    
    code.append("start:")
    code.append("    invoke SetConsoleOutputCP, 65001")
    code.append("    invoke GetStdHandle, STD_OUTPUT_HANDLE")
    code.append("    mov rbx, rax") 
    code.append("    invoke GetStdHandle, STD_INPUT_HANDLE")
    code.append("    mov rsi, rax") 

    for k, v in variables.items():
        if v['type'] == 'string':
            clean_val = str(v['value']).strip('"')
            data.append(f"var_{k} db '{clean_val}',0\nvar_{k}_len = $ - var_{k} - 1")
        elif v['type'] == 'int': data.append(f"var_{k} dq {v['value']}")
        elif v['type'] == 'boolean': data.append(f"var_{k} db {v['value']}")
        elif v['type'] == 'input_string':
            clean_prompt = str(v['value']).strip('"')
            data.append(f"prompt_{k} db '{clean_prompt}',0\nprompt_{k}_len = $ - prompt_{k} - 1")
            data.append(f"var_{k} db 256 dup (0)\nvar_{k}_len dq 0\nread_{k} dq 0")

    label_stack = []
    label_counter = 0

    for i, cmd in enumerate(commands):
        if cmd['type'] == 'if_start':
            lbl = label_counter
            label_counter += 1
            label_stack.append(lbl)
            clean_val = str(cmd['val']).strip('"')
            data.append(f"if_const_{lbl} db '{clean_val}',0\nif_const_len_{lbl} = $ - if_const_{lbl} - 1")
            code.append(f"    mov rsi, var_{cmd['var']}\n    mov rdi, if_const_{lbl}\n    mov rcx, [var_{cmd['var']}_len]\n    cmp rcx, if_const_len_{lbl}\n    jne .else_{lbl}\n    repe cmpsb\n    jne .else_{lbl}")
            
        elif cmd['type'] == 'else_start':
            if label_stack:
                lbl = label_stack[-1]
                code.append(f"    jmp .end_if_{lbl}\n.else_{lbl}:")
                
        elif cmd['type'] == 'block_end':
            if label_stack:
                lbl = label_stack.pop()
                if any(f"jmp .end_if_{lbl}" in line for line in code):
                    code.append(f".end_if_{lbl}:")
                else:
                    code.append(f".else_{lbl}:\n.end_if_{lbl}:")

        elif cmd['type'] == 'sys_input':
            k = cmd['var']
            code.append(f"    invoke WriteFile, rbx, prompt_{k}, prompt_{k}_len, read_{k}, 0")
            code.append(f"    invoke ReadConsoleA, rsi, var_{k}, 255, read_{k}, 0")
            code.append(f"    mov rcx, [read_{k}]\n    sub rcx, 2\n    mov [var_{k}_len], rcx\n    mov byte [var_{k} + rcx], 0")

        elif cmd['type'] == 'sys_pause':
            # Добавляем строку аргумента для функции system()
            data.append(f"cmd_pause_{i} db 'pause',0")
            
            # Настоящий, железобетонный вызов C-функции system("pause")
            code.append(f"    sub rsp, 40")  # Выравниваем стек и выделяем теневое пространство
            code.append(f"    lea rcx, [cmd_pause_{i}]")
            code.append(f"    call [crt_system]")
            code.append(f"    add rsp, 40")

        elif cmd['type'] in ['raw_string', 'concat', 'expr']:
            data.append(f"written_{i} dq 0")
            
            if cmd['type'] == 'raw_string': 
                clean_txt = str(cmd['value']).strip('"')
                data.append(f"msg_{i} db '{clean_txt}',13,10\nmsg_{i}_len = $ - msg_{i}")
                code.append(f"    invoke WriteFile, rbx, msg_{i}, msg_{i}_len, written_{i}, 0")
                
            elif cmd['type'] == 'concat':
                for sub_idx, p in enumerate(cmd['value']):
                    if p.startswith("[") and p.endswith("]"):
                        v_name = p[1:-1].strip()
                        if variables[v_name]['type'] == 'input_string':
                            code.append(f"    invoke WriteFile, rbx, var_{v_name}, [var_{v_name}_len], written_{i}, 0")
                        else:
                            static_text = str(variables[v_name]['value']).strip('"')
                            data.append(f"msg_sub_{i}_{v_name}_{sub_idx} db '{static_text}',0\nmsg_sub_{i}_{v_name}_{sub_idx}_len = $ - msg_sub_{i}_{v_name}_{sub_idx} - 1")
                            code.append(f"    invoke WriteFile, rbx, msg_sub_{i}_{v_name}_{sub_idx}, msg_sub_{i}_{v_name}_{sub_idx}_len, written_{i}, 0")
                    else:
                        raw_text = p.strip('"')
                        data.append(f"msg_sub_raw_{i}_{sub_idx} db '{raw_text}',0\nmsg_sub_raw_{i}_{sub_idx}_len = $ - msg_sub_raw_{i}_{sub_idx} - 1")
                        code.append(f"    invoke WriteFile, rbx, msg_sub_raw_{i}_{sub_idx}, msg_sub_raw_{i}_{sub_idx}_len, written_{i}, 0")
                data.append(f"crlf_{i} db 13,10")
                code.append(f"    invoke WriteFile, rbx, crlf_{i}, 2, written_{i}, 0")
                
            elif cmd['type'] == 'expr': 
                expr = cmd['value']
                if expr in variables and variables[expr]['type'] == 'input_string':
                    data.append(f"crlf_expr_{i} db 13,10")
                    code.append(f"    invoke WriteFile, rbx, var_{expr}, [var_{expr}_len], written_{i}, 0\n    invoke WriteFile, rbx, crlf_expr_{i}, 2, written_{i}, 0")
                else:
                    if expr in variables:
                        text = str(variables[expr]['value']).strip('"')
                    else:
                        expr_resolved = expr
                        for v_name in sorted(variables.keys(), key=len, reverse=True):
                            pattern = rf"\b{re.escape(v_name)}\b"
                            if re.search(pattern, expr_resolved):
                                expr_resolved = re.sub(pattern, str(variables[v_name]['value']), expr_resolved)
                        try: text = str(eval(expr_resolved))
                        except: text = cmd['value']
                            
                    data.append(f"msg_{i} db '{text}',13,10\nmsg_{i}_len = $ - msg_{i}")
                    code.append(f"    invoke WriteFile, rbx, msg_{i}, msg_{i}_len, written_{i}, 0")

    code.append("    invoke ExitProcess, 0")

    return f"""format PE64 CONSOLE
entry start
include 'win64a.inc'
section '.data' data readable writeable
{chr(10).join(data)}
section '.code' code readable executable
{chr(10).join(code)}
section '.idata' import data readable writeable
library kernel32, 'KERNEL32.DLL', \\
        msvcrt, 'MSVCRT.DLL'

import kernel32, \\
    GetStdHandle, 'GetStdHandle', \\
    WriteFile, 'WriteFile', \\
    ReadConsoleA, 'ReadConsoleA', \\
    SetConsoleOutputCP, 'SetConsoleOutputCP', \\
    ExitProcess, 'ExitProcess'

import msvcrt, \\
    crt_system, 'system'
"""

def build():
    if not os.path.exists("Compiler"): os.makedirs("Compiler")
    if not os.path.exists(INPUT_FILE): return
    with open(INPUT_FILE, "r", encoding="utf-8") as f: code = f.read()
    vars, cmds = parse_code(code)
    with open(ASM_FILE, "w", encoding="utf-8") as f: f.write(generate_fasm(vars, cmds))
    if os.path.exists(EXE_FILE): os.remove(EXE_FILE)
    
    result = subprocess.run([FASM_PATH, ASM_FILE, EXE_FILE], capture_output=True)
    if result.returncode == 0: 
        print(" [SUCCESS] Parsed and compiled successfully!")
    else:
        print(" [FASM ERROR]")
        print(result.stderr.decode('cp866', errors='ignore'))

if __name__ == "__main__": build()
