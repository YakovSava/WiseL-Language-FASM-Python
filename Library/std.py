# Compiler/std.py

def generate_single_command(cmd, variables, i):
    """
    Генерирует data и code строго для одной переданной команды
    """
    data, code = [], []
    
    if cmd['type'] == 'sys_input':
        k = cmd['var']
        if cmd['v_type'] == 'string':
            code.append(f"    invoke WriteFile, rbx, prompt_{k}, prompt_{k}_len, read_{k}, 0")
            code.append(f"    invoke ReadConsoleA, rsi, var_{k}, 255, read_{k}, 0")
            code.append(f"    mov rcx, [read_{k}]\n    sub rcx, 2\n    mov [var_{k}_len], rcx\n    mov byte [var_{k} + rcx], 0")
        elif cmd['v_type'] == 'int':
            code.append(f"    invoke WriteFile, rbx, prompt_{k}, prompt_{k}_len, read_{k}, 0")
            code.append(f"    invoke ReadConsoleA, rsi, buf_{k}, 63, read_{k}, 0")
            code.append(f"    mov rcx, [read_{k}]\n    sub rcx, 2\n    mov byte [buf_{k} + rcx], 0")
            code.append(f"    sub rsp, 40\n    lea rcx, [buf_{k}]\n    lea rdx, [num_fmt]\n    lea r8, [var_{k}]\n    call [crt_sscanf]\n    add rsp, 40")

    elif cmd['type'] == 'sys_pause':
        data.append(f"cmd_pause_{i} db 'pause',0")
        code.append(f"    sub rsp, 40\n    lea rcx, [cmd_pause_{i}]\n    call [crt_system]\n    add rsp, 40")

    elif cmd['type'] in ['raw_string', 'concat', 'expr']:
        data.append(f"written_{i} dq 0")
        
        if cmd['type'] == 'raw_string': 
            data.append(f"msg_{i} db '{cmd['value']}',13,10\nmsg_{i}_len = $ - msg_{i}")
            code.append(f"    invoke WriteFile, rbx, msg_{i}, msg_{i}_len, written_{i}, 0")
            
        elif cmd['type'] == 'concat':
            for sub_idx, p in enumerate(cmd['value']):
                if p.startswith("[") and p.endswith("]"):
                    expr = p[1:-1].strip()
                    op = next((possible_op for possible_op in ['+', '-', '/', '*'] if possible_op in expr), None)
                    
                    if op:
                        v1, v2 = [part.strip() for part in expr.split(op)]
                        code.append(f"    mov rax, [var_{v1}]")
                        if op == '+': code.append(f"    add rax, [var_{v2}]")
                        elif op == '-': code.append(f"    sub rax, [var_{v2}]")
                        elif op == '*': code.append(f"    imul rax, [var_{v2}]")
                        elif op == '/':
                            code.append(f"    xor rdx, rdx") 
                            code.append(f"    idiv qword [var_{v2}]")
                            
                        code.append(f"    sub rsp, 40\n    lea rcx, [calc_buf]\n    lea rdx, [num_fmt]\n    mov r8, rax\n    call [crt_sprintf]\n    add rsp, 40")
                        code.append(f"    sub rsp, 40\n    lea rcx, [calc_buf]\n    call [crt_strlen]\n    add rsp, 40")
                        code.append(f"    mov [written_{i}], rax")
                        code.append(f"    invoke WriteFile, rbx, calc_buf, [written_{i}], written_{i}, 0")
                    else:
                        v_name = expr
                        if variables.get(v_name, {}).get('type') == 'input_string':
                            code.append(f"    invoke WriteFile, rbx, var_{v_name}, [var_{v_name}_len], written_{i}, 0")
                else:
                    raw_text = p.strip('"')
                    data.append(f"msg_sub_raw_{i}_{sub_idx} db '{raw_text}',0\nmsg_sub_raw_{i}_{sub_idx}_len = $ - msg_sub_raw_{i}_{sub_idx} - 1")
                    code.append(f"    invoke WriteFile, rbx, msg_sub_raw_{i}_{sub_idx}, msg_sub_raw_{i}_{sub_idx}_len, written_{i}, 0")
            data.append(f"crlf_{i} db 13,10")
            code.append(f"    invoke WriteFile, rbx, crlf_{i}, 2, written_{i}, 0")

    return data, code
