# Library/WinX64.py
"""Окна, оконная процедура, сборка FASM"""
import re
import Fluent
import Fluent_uix
import FluentFuncX64

def parse_windows(code):
    wins = {}
    current_win = None
    for raw in code.splitlines():
        line = raw.strip()
        if not line or line.startswith("Use") or line.startswith("init") or line.startswith("#"):
            continue
        m = re.match(r"window\s+(\w+)\s*:", line)
        if m:
            current_win = m.group(1)
            wins[current_win] = {"title": "Wise Window", "width": 400, "height": 300, "bg": "COLOR_WINDOW + 1", "is_hex": False}
            continue
        if re.match(r"\w+\.(addFluentButton|onHover|addFunction|show)\s*[:\(]", line):
            current_win = None
            continue
        if current_win and current_win in wins and "=" in line:
            if "title" in line:
                m = re.search(r'title\s*=\s*"(.*?)"', line)
                if m: wins[current_win]["title"] = m.group(1)
            elif "width" in line:
                m = re.search(r'width\s*=\s*(\d+)', line)
                if m: wins[current_win]["width"] = m.group(1)
            elif "height" in line:
                m = re.search(r'height\s*=\s*(\d+)', line)
                if m: wins[current_win]["height"] = m.group(1)
            elif "background" in line:
                m = re.search(r'background\s*=\s*"(.*?)"', line)
                if m:
                    v = m.group(1)
                    if v.startswith("#"):
                        wins[current_win]["bg"] = Fluent.hex_to_bgr(v)
                        wins[current_win]["is_hex"] = True
                    elif v == "white": wins[current_win]["bg"] = "COLOR_WINDOW + 1"
                    elif v == "black": wins[current_win]["bg"] = "COLOR_WINDOW + 4"
    return wins

def gen_window_data(name, props):
    return [
        f"  _class_{name} du 'Class_{name}',0",
        f"  _title_{name} du '{props['title']}',0",
        f"  wc_{name} WNDCLASS",
        f"  hwnd_{name} dq 0"
    ]

def gen_window_create(name, props):
    code = [
        f"    mov [wc_{name}.style], CS_HREDRAW or CS_VREDRAW",
        f"    mov [wc_{name}.lpfnWndProc], WindowProc_{name}",
        f"    invoke GetModuleHandle, 0",
        f"    mov [wc_{name}.hInstance], rax",
        f"    invoke LoadIcon, 0, IDI_APPLICATION",
        f"    mov [wc_{name}.hIcon], rax",
        f"    invoke LoadCursor, 0, IDC_ARROW",
        f"    mov [wc_{name}.hCursor], rax"
    ]
    if props["is_hex"]:
        code += [f"    invoke CreateSolidBrush, {props['bg']}", f"    mov [wc_{name}.hbrBackground], rax"]
    else:
        code.append(f"    mov [wc_{name}.hbrBackground], {props['bg']}")
    code += [
        f"    mov [wc_{name}.lpszClassName], _class_{name}",
        f"    lea rcx, [wc_{name}]",
        f"    invoke RegisterClass, rcx",
        f"    test eax, eax",
        f"    jz exit",
        f"    invoke CreateWindowEx, 0, _class_{name}, _title_{name}, \\",
        f"           WS_OVERLAPPEDWINDOW or WS_VISIBLE, \\",
        f"           CW_USEDEFAULT, CW_USEDEFAULT, {props['width']}, {props['height']}, \\",
        f"           0, 0, [wc_{name}.hInstance], 0",
        f"    test rax, rax",
        f"    jz exit",
        f"    mov [hwnd_{name}], rax"
    ]
    return code

def gen_window_proc(name, widgets, functions):
    code = [
        f"proc WindowProc_{name} hwnd, wmsg, wparam, lparam",
        f"    push rbx rsi rdi r14",
        f"    mov rbx, rcx",
        f"    mov rsi, rdx",
        f"    mov rdi, r8",
        f"    mov r14, r9",
        f"    cmp edx, 1",
        f"    je .wm_create",
        f"    cmp edx, 15",
        f"    je .wm_paint",
        f"    cmp edx, 512",
        f"    je .wm_mousemove",
        f"    cmp edx, 513",
        f"    je .wm_lbuttondown",
        f"    cmp edx, WM_DESTROY",
        f"    je .wm_destroy",
        f"    pop r14 rdi rsi rbx",
        f"    invoke DefWindowProc, rcx, rdx, r8, r9",
        f"    ret",
        f"  .wm_create:",
        f"    invoke CreateFont, 16, 0, 0, 0, 400, 0, 0, 0, 204, 0, 0, 5, 0, sys_font_name",
        f"    mov [hFont], rax",
        f"    xor eax, eax",
        f"    jmp .finish",
        f"  .wm_paint:",
        f"    lea rdx, [ps]",
        f"    invoke BeginPaint, rbx, rdx",
        f"    mov r12, rax",
        f"    invoke SelectObject, r12, [hFont]",
        f"    invoke SetBkMode, r12, 1"
    ]
    code += Fluent_uix.gen_paint(widgets)
    code += [
        f"    lea rdx, [ps]",
        f"    invoke EndPaint, rbx, rdx",
        f"    xor eax, eax",
        f"    jmp .finish",
        f"  .wm_mousemove:",
        f"    mov rdx, r14",
        f"    movzx eax, dx",
        f"    shr rdx, 16",
        f"    movzx edx, dx"
    ]
    code += Fluent_uix.gen_mousemove(widgets)
    code += [
        f"    xor eax, eax",
        f"    jmp .finish",
        f"  .wm_lbuttondown:",
        f"    mov rdx, r14",
        f"    movzx eax, dx",
        f"    shr rdx, 16",
        f"    movzx edx, dx"
    ]
    code += FluentFuncX64.generate_click_handler(widgets, functions)
    code += [
        f"    xor eax, eax",
        f"    jmp .finish",
        f"  .wm_destroy:",
        f"    dec qword [sys_win_count]",
        f"    cmp qword [sys_win_count], 0",
        f"    jne .skip_quit",
        f"    invoke PostQuitMessage, 0",
        f"  .skip_quit:",
        f"    xor eax, eax",
        f"  .finish:",
        f"    pop r14 rdi rsi rbx",
        f"    ret",
        f"endp"
    ]
    return code

def build(code):
    wins = parse_windows(code)
    widgets_map = Fluent_uix.parse(code)
    
    all_widgets = []
    for wlist in widgets_map.values():
        for w in wlist:
            Fluent.finalize_props(w)
            all_widgets.append(w)
    
    temp_lookup = {w["name"]: w for w in all_widgets}
    id_map = {w["name"]: w["id"] for w in all_widgets}
    counter = max([int(w["id"]) for w in all_widgets]) if all_widgets else 1000
    
    functions = FluentFuncX64.parse_functions(code, temp_lookup, id_map, counter)

    for w in all_widgets:
        Fluent.finalize_props(w)
    
    for name, wlist in widgets_map.items():
        if name in wins:
            wins[name]["widgets"] = wlist
            wins[name]["functions"] = functions

    data = Fluent.data_section()
    data.append(f"sys_win_count dq {len(wins)}")
    asm = ["start:", "    sub rsp, 8*5"]

    for name, props in wins.items():
        data += gen_window_data(name, props)
        data += Fluent_uix.gen_data(props.get("widgets", []))

    for name, props in wins.items():
        asm += gen_window_create(name, props)

    asm += [
        "  msg_loop:",
        "    lea rcx, [msg]",
        "    invoke GetMessage, rcx, 0, 0, 0",
        "    test eax, eax",
        "    jz exit",
        "    lea rcx, [msg]",
        "    invoke TranslateMessage, rcx",
        "    lea rcx, [msg]",
        "    invoke DispatchMessage, rcx",
        "    jmp msg_loop",
        "  exit:",
        "    mov rcx, [msg.wParam]",
        "    invoke ExitProcess, rcx"
    ]

    for name, props in wins.items():
        asm += gen_window_proc(name, props.get("widgets", []), props.get("functions", {}))

    return f"""format PE64 GUI 5.0
entry start

include 'win64w.inc'

section '.data' data readable writeable
{chr(10).join(data)}

section '.code' code readable executable
{chr(10).join(asm)}

section '.idata' import data readable writeable
  library kernel32, 'KERNEL32.DLL', \\
          user32,   'USER32.DLL',   \\
          gdi32,    'GDI32.DLL'

  include 'api\\\\kernel32.inc'
  include 'api\\\\user32.inc'
  include 'api\\\\gdi32.inc'
"""