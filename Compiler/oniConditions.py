import re

def parse_line(line, variables):
    if line.startswith("if"):
        match = re.match(r"if\s+\[(\w+)\]\s*==\s*\"(.*?)\"\s*\{", line)
        if match:
            var_name, target_str = match.groups()
            return True, {'type': 'if_start', 'var': var_name, 'val': target_str}
            
    if line.startswith("} else {"):
        return True, {'type': 'else_start'}

    if line == "}":
        return True, {'type': 'block_end'}

    return False, None
