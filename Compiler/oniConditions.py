# Compiler/oniConditions.py
import re

def parse_line(line, variables):
    if line.startswith("if"):
        match = re.match(r"if\s+\[(\w+)\]\s*(==|!=|>=|<=|>|<)\s*\"?(.*?)\"?\s*\{", line)
        if match:
            var_name, op, value = match.groups()
            var_info = variables.get(var_name, {})
            var_type = var_info.get('type', '')
            
            if var_type == 'input_string':
                return True, {
                    'type': 'if_start',
                    'var': var_name,
                    'op': op,
                    'val': value,
                    'is_dynamic': True,
                    'met': True
                }
            
            if var_type == 'string':
                var_val = str(var_info.get('value', ''))
                value_str = str(value)
                condition_met = (var_val == value_str) if op == "==" else (var_val != value_str)
                return True, {
                    'type': 'if_start',
                    'var': var_name,
                    'op': op,
                    'val': value,
                    'is_dynamic': False,
                    'met': condition_met
                }
            
            if var_type == 'int':
                var_val = int(var_info.get('value', 0))
                value_int = int(value)
                if op == "==": condition_met = (var_val == value_int)
                elif op == "!=": condition_met = (var_val != value_int)
                elif op == ">": condition_met = (var_val > value_int)
                elif op == "<": condition_met = (var_val < value_int)
                elif op == ">=": condition_met = (var_val >= value_int)
                elif op == "<=": condition_met = (var_val <= value_int)
                return True, {
                    'type': 'if_start',
                    'var': var_name,
                    'op': op,
                    'val': value,
                    'is_dynamic': False,
                    'met': condition_met
                }
            
            return True, {
                'type': 'if_start',
                'var': var_name,
                'op': op,
                'val': value,
                'is_dynamic': True,
                'met': True
            }
    
    if line.startswith("} else {"):
        return True, {'type': 'else_start'}
    
    if line == "}":
        return True, {'type': 'block_end'}
    
    return False, None