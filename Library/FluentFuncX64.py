# Library/FluentFuncX64.py
"""Обработчики событий: onClick с поддержкой if/else и переменных"""
import re
import Fluent

def parse_functions(code, temp_widgets, id_map, counter):
    functions = {}
    variables = {}
    current_btn = None
    current_event = None
    in_if = False
    in_else = False
    skip_if = False
    
    for raw in code.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        
        # string a = "123"
        m = re.match(r'string\s+(\w+)\s*=\s*"(.*?)"', line)
        if m:
            variables[m.group(1)] = m.group(2)
            continue
        
        m = re.match(r"(\w+)\.addFunction\((\w+)\)\s*:", line)
        if m:
            current_btn = m.group(1)
            current_event = m.group(2)
            in_if = in_else = skip_if = False
            if current_btn not in functions:
                functions[current_btn] = {}
            functions[current_btn][current_event] = True
            continue
        
        if current_btn and current_event:
            # if [a] == "123":
            m_if = re.match(r'if\s+\[(\w+)\]\s*(==|!=)\s*"(.*?)"', line)
            if m_if:
                var_name, op, val = m_if.groups()
                if var_name in variables:
                    if op == "==":
                        in_if = True
                        in_else = False
                        skip_if = (variables[var_name] != val)
                    elif op == "!=":
                        in_if = True
                        in_else = False
                        skip_if = (variables[var_name] == val)
                continue
            
            # else:
            if line == "else:":
                in_if = False
                in_else = True
                skip_if = not skip_if
                continue
            
            if line == "}" or line == "};":
                in_if = in_else = skip_if = False
                continue
            
            if skip_if:
                continue
            
            if "=" in line:
                rest = line.strip()
                
                m_target = re.match(r"(\w+)\.(\w+)\s*=\s*(.+)", rest)
                if m_target:
                    target_name = m_target.group(1)
                    prop = m_target.group(2)
                    val = m_target.group(3).strip().strip('"')
                    if target_name in temp_widgets:
                        Fluent.apply_props(temp_widgets[target_name], "onClick", f"{prop} = {val}")
                    continue
                
                if rest.startswith("hover."):
                    prop_val = rest[6:]
                    if current_btn in temp_widgets:
                        Fluent.apply_props(temp_widgets[current_btn], current_event, prop_val, sub_event="hover")
                    continue
                
                if current_btn in temp_widgets:
                    Fluent.apply_props(temp_widgets[current_btn], current_event, rest)
                continue
        
        if re.match(r"(window\s+|Form\d+\.|Button\d+\.)", line) and "addFunction" not in line:
            current_btn = current_event = None
            in_if = in_else = skip_if = False
    
    return functions

def generate_click_handler(widgets, functions):
    code = []
    name_to_widget = {w.get("name", ""): w for w in widgets}
    
    for w in widgets:
        name = w.get("name", "")
        if name in functions and "onClick" in functions[name]:
            wid = w["id"]
            
            code += [
                f"    cmp eax, [btn_rect_{wid}.left]",
                f"    jl .skip_click_{wid}",
                f"    cmp eax, [btn_rect_{wid}.right]",
                f"    jg .skip_click_{wid}",
                f"    cmp edx, [btn_rect_{wid}.top]",
                f"    jl .skip_click_{wid}",
                f"    cmp edx, [btn_rect_{wid}.bottom]",
                f"    jg .skip_click_{wid}",
            ]
            
            for other_name, other_w in name_to_widget.items():
                other_wid = other_w["id"]
                code += [
                    f"    lea rcx, [btn_rect_{other_wid}]",
                    f"    invoke InvalidateRect, rbx, rcx, 0",
                ]
            
            for other_name, other_w in name_to_widget.items():
                other_wid = other_w["id"]
                if other_w.get("click_x") != other_w.get("x"):
                    new_x = other_w.get("click_x", other_w.get("x", 0))
                    new_w = other_w.get("click_w", other_w.get("w", 100))
                    code += [
                        f"    mov dword [btn_rect_{other_wid}.left], {new_x}",
                        f"    mov dword [btn_rect_{other_wid}.right], {new_x + new_w}",
                    ]
                if other_w.get("click_y") != other_w.get("y"):
                    new_y = other_w.get("click_y", other_w.get("y", 0))
                    new_h = other_w.get("click_h", other_w.get("h", 30))
                    code += [
                        f"    mov dword [btn_rect_{other_wid}.top], {new_y}",
                        f"    mov dword [btn_rect_{other_wid}.bottom], {new_y + new_h}",
                    ]
            
            code.append(f"    mov [btn_state_{wid}], 2")
            
            for other_name, other_w in name_to_widget.items():
                if other_name != name:
                    other_wid = other_w["id"]
                    if other_w.get("click_bg") != other_w.get("bg") or other_w.get("click_x") != other_w.get("x"):
                        code.append(f"    mov [btn_state_{other_wid}], 2")
            
            code += [
                f"    invoke InvalidateRect, rbx, 0, 1",
                f"    invoke UpdateWindow, rbx",
                f"  .skip_click_{wid}:"
            ]
    
    return code