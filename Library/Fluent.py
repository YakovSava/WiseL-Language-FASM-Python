# Library/Fluent.py

PROPS_MAP = {
    "title": "text",
    "x": "x", "y": "y",
    "width": "w", "height": "h",
    "background": "bg",
    "font_color": "font_color",
    "border_color": "border_color"
}

EVENT_PREFIX = {
    None: "",
    "onHover": "hover_",
    "onClick": "click_",
    "onLeave": "leave_",
    "onFocus": "focus_"
}

DEFAULTS = {
    "text": "Button", "x": 0, "y": 0, "w": 100, "h": 30,
    "bg": "#2D2D2D", "font_color": "#FFFFFF", "border_color": "#3F3F46"
}

def hex_to_bgr(hex_color):
    c = hex_color.replace("#", "").replace('"', "").strip()
    return f"0x00{c[4:6]}{c[2:4]}{c[0:2]}"

def data_section():
    return [
        "msg MSG",
        "ps PAINTSTRUCT",
        "rct RECT",
        "border_rect RECT",
        "sys_font_name du 'Segoe UI',0",
        "hFont dq 0"
    ]

def create_widget(name, id_map, counter):
    if name not in id_map:
        counter += 1
        id_map[name] = str(counter)
    
    w = {"type": "fluent_btn", "id": id_map[name], "name": name}
    
    for prop, default in DEFAULTS.items():
        w[prop] = default
    
    for event, prefix in EVENT_PREFIX.items():
        if event:
            for prop in ["text", "x", "y", "w", "h", "bg", "font_color", "border_color"]:
                w[prefix + prop] = None
    
    # Добавляем click_hover_ свойства
    for prop in ["bg", "font_color", "border_color"]:
        w["click_hover_" + prop] = None
    
    return w, counter

def apply_props(w, event, line, sub_event=None):
    if sub_event == "hover":
        prefix = EVENT_PREFIX.get(event, "") + "hover_"
    else:
        prefix = EVENT_PREFIX.get(event, "")
    k, v = line.split("=", 1)
    k, v = k.strip(), v.strip().strip('"')
    if k in PROPS_MAP:
        key = prefix + PROPS_MAP[k]
        w[key] = int(v) if k in ("x", "y", "width", "height") else v

def finalize_props(w):
    for event, prefix in EVENT_PREFIX.items():
        if event:
            for prop in ["text", "x", "y", "w", "h", "bg", "font_color", "border_color"]:
                key = prefix + prop
                if key not in w or w[key] is None:
                    w[key] = w.get(prop, DEFAULTS.get(prop, ""))
    
    # click_hover_ → click_ (или обычные если click_ нет)
    for prop in ["bg", "font_color", "border_color"]:
        key = "click_hover_" + prop
        if key not in w or w[key] is None:
            w[key] = w.get("hover_" + prop, w.get(prop, DEFAULTS.get(prop, "")))

def widget_data(w):
    wid = w["id"]
    lines = []
    
    # Обычный текст
    utf16 = [f"0x{ord(c):04X}" for c in str(w.get("text", "Button"))] + ["0"]
    lines.append(f"  _btn_text_{wid} dw {', '.join(utf16)}")
    lines.append(f"  btn_rect_{wid} RECT {w.get('x', 0)}, {w.get('y', 0)}, {w.get('x', 0) + w.get('w', 100)}, {w.get('y', 0) + w.get('h', 30)}")
    lines.append(f"  btn_state_{wid} dd 0")
    
    # Цвета обычные
    lines.append(f"  btn_bg_{wid} dd {hex_to_bgr(w.get('bg', '#2D2D2D'))}")
    lines.append(f"  btn_font_{wid} dd {hex_to_bgr(w.get('font_color', '#FFFFFF'))}")
    lines.append(f"  btn_border_{wid} dd {hex_to_bgr(w.get('border_color', '#3F3F46'))}")
    
    # Ховер
    lines.append(f"  btn_bg_hover_{wid} dd {hex_to_bgr(w.get('hover_bg', w.get('bg', '#2D2D2D')))}")
    lines.append(f"  btn_font_hover_{wid} dd {hex_to_bgr(w.get('hover_font', w.get('font_color', '#FFFFFF')))}")
    lines.append(f"  btn_rect_hover_{wid} RECT {w.get('x', 0)}, {w.get('y', 0)}, {w.get('x', 0) + w.get('w', 100)}, {w.get('y', 0) + w.get('h', 30)}")
    
    # Клик
    click_text = w.get('click_text', w.get('text', 'Button'))
    utf16_click = [f"0x{ord(c):04X}" for c in str(click_text)] + ["0"]
    lines.append(f"  _btn_text_click_{wid} dw {', '.join(utf16_click)}")
    cx = w.get('click_x', w.get('x', 0))
    cy = w.get('click_y', w.get('y', 0))
    cw = w.get('click_w', w.get('w', 100))
    ch = w.get('click_h', w.get('h', 30))
    lines.append(f"  btn_rect_click_{wid} RECT {cx}, {cy}, {cx + cw}, {cy + ch}")
    lines.append(f"  btn_bg_click_{wid} dd {hex_to_bgr(w.get('click_bg', w.get('bg', '#2D2D2D')))}")
    lines.append(f"  btn_font_click_{wid} dd {hex_to_bgr(w.get('click_font', w.get('font_color', '#FFFFFF')))}")
    lines.append(f"  btn_border_click_{wid} dd {hex_to_bgr(w.get('click_border', w.get('border_color', '#3F3F46')))}")
    
    # Ховер внутри клика
    lines.append(f"  btn_bg_click_hover_{wid} dd {hex_to_bgr(w.get('click_hover_bg', w.get('click_bg', w.get('bg', '#2D2D2D'))))}")
    lines.append(f"  btn_font_click_hover_{wid} dd {hex_to_bgr(w.get('click_hover_font', w.get('click_font', w.get('font_color', '#FFFFFF'))))}")
    lines.append(f"  btn_border_click_hover_{wid} dd {hex_to_bgr(w.get('click_hover_border', w.get('click_border', w.get('border_color', '#3F3F46'))))}")
    lines.append(f"  btn_rect_click_hover_{wid} RECT {cx}, {cy}, {cx + cw}, {cy + ch}")
    
    return lines