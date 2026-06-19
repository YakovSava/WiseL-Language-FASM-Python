# Library/Fluent_uix.py

import re
import Fluent
import Fluent_core

def parse(code):
    widgets = {}
    current_win = None
    current_btn = None
    current_hover = None
    temp = {}
    id_map = {}
    counter = 1000

    for raw in code.splitlines():
        line = raw.strip()
        if not line or line.startswith("Use") or line.startswith("init") or line.startswith("#"):
            continue

        m = re.match(r"window\s+(\w+)\s*:", line)
        if m:
            current_win = m.group(1)
            current_btn = current_hover = None
            widgets.setdefault(current_win, [])
            continue

        m = re.match(r"(\w+)\.addFluentButton\s*:", line)
        if m:
            name = m.group(1)
            current_btn = name
            current_hover = None
            current_win = None
            if name not in temp:
                temp[name], counter = Fluent.create_widget(name, id_map, counter)
            continue

        m = re.match(r"(\w+)\.onHover\s*:", line)
        if m:
            current_hover = m.group(1)
            current_btn = None
            current_win = None
            if current_hover not in temp:
                temp[current_hover], counter = Fluent.create_widget(current_hover, id_map, counter)
            continue

        # Пропускаем addFunction
        if re.match(r"\w+\.addFunction\(\w+\)\s*:", line):
            current_btn = current_hover = None
            continue

        if current_btn and current_btn in temp and "=" in line:
            Fluent.apply_props(temp[current_btn], None, line)
            continue

        if current_hover and current_hover in temp and "=" in line:
            Fluent.apply_props(temp[current_hover], "onHover", line)
            continue

        m = re.match(r"(\w+)\.show\s*\(\s*\)", line)
        if m:
            win = m.group(1)
            for b_name, b in list(temp.items()):
                Fluent.finalize_props(b)
                widgets.setdefault(win, []).append(b)
                del temp[b_name]
            current_btn = current_hover = current_win = None

    return widgets

def gen_data(widgets_list):
    data = []
    for w in widgets_list:
        if w["type"] == "fluent_btn":
            data += Fluent.widget_data(w)
    return data

def gen_paint(widgets_list):
    code = []
    for w in widgets_list:
        if w["type"] == "fluent_btn":
            code += Fluent_core.paint(w["id"])
    return code

def gen_mousemove(widgets_list):
    code = []
    for w in widgets_list:
        if w["type"] == "fluent_btn":
            code += Fluent_core.mousemove(w["id"])
    return code