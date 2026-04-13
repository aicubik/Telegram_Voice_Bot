import zlib
import phpserialize

def traverse_and_extract(node, depth=0):
    text = ""
    prefix = "  " * depth
    if isinstance(node, dict):
        # Decode byte keys and values
        new_node = {}
        for k, v in node.items():
            key_str = k.decode('utf-8', errors='ignore') if isinstance(k, bytes) else str(k)
            new_node[key_str] = v
            
        b_type = ""
        if 'Type' in new_node and isinstance(new_node['Type'], bytes): b_type = new_node['Type'].decode('utf-8', errors='ignore')
        b_name = ""
        if 'Name' in new_node and isinstance(new_node['Name'], bytes): b_name = new_node['Name'].decode('utf-8', errors='ignore')
        
        if b_type or b_name:
            text += f"{prefix}[Блок: {b_type}] {b_name}\n"
            
        if 'Properties' in new_node and isinstance(new_node['Properties'], dict):
            props = new_node['Properties']
            for pk, pv in props.items():
                k_str = pk.decode('utf-8', errors='ignore') if isinstance(pk, bytes) else str(pk)
                # print readable values
                if isinstance(pv, bytes):
                    v_str = pv.decode('utf-8', errors='ignore')
                    if len(v_str) > 2 and not v_str.isnumeric():
                        text += f"{prefix}  - {k_str}: {v_str}\n"
                elif isinstance(pv, dict) or isinstance(pv, list) or isinstance(pv, tuple):
                     pass # handled lower
                    
        # Recursively traverse
        for pk, pv in new_node.items():
            if isinstance(pv, (dict, list, tuple)):
                # don't increase depth unless it's Children
                if pk == 'Children':
                    text += traverse_and_extract(pv, depth+1)
                else:
                    text += traverse_and_extract(pv, depth)
                    
    elif isinstance(node, (list, tuple)):
        
        if hasattr(node, 'values'):
           vs = list(node.values())
        else:
           vs = node
           
        for item in vs:
            text += traverse_and_extract(item, depth)
            
    return text

with open('bp-204.bpt', 'rb') as f:
    data = f.read()

try:
    dec = zlib.decompress(data)
    parsed = phpserialize.loads(dec)
    
    # We are interested in templates and variables
    output = "--- ПЕРЕМЕННЫЕ И ПАРАМЕТРЫ ---\n"
    if b'VARIABLES' in parsed and isinstance(parsed[b'VARIABLES'], dict):
       for k,v in parsed[b'VARIABLES'].items():
           if isinstance(v, dict) and b'Name' in v:
              output += f"Var: {v[b'Name'].decode('utf-8', errors='ignore')}\n"
              
    output += "\n--- ШАГИ БИЗНЕС-ПРОЦЕССА ---\n"
    if b'TEMPLATE' in parsed:
        output += traverse_and_extract(parsed[b'TEMPLATE'])
        
    print(output)
except Exception as e:
    print(e)
