def flatten_dict(input_dict, separator="/"):
    flattened_dict = {}
    stack = [(key, value) for key, value in input_dict.items()]
    while stack:
        current_key, current_value = stack.pop()
        if isinstance(current_value, dict):
            for k, v in current_value.items():
                new_key = current_key + separator + k if current_key else k
                stack.append((new_key, v))
        else:
            flattened_dict[separator + current_key] = current_value
    return flattened_dict

def unflatten_dict(flattened_dict, separator="/"):
    unflattened_dict = {}
    for key, value in flattened_dict.items():
        parts = key.split(separator)
        current_dict = unflattened_dict
        for part in parts[1:-1]:
            if part not in current_dict:
                current_dict[part] = {}
            current_dict = current_dict[part]
        current_dict[parts[-1]] = value
    return unflattened_dict

input_dict = {
    "obj_a": {"pos": {"x": 0.2, "y": 0.3, "z": 0.4}},
    "val_b": True
}

flattened_dict = flatten_dict(input_dict)
print(flattened_dict)

original_dict = unflatten_dict(flattened_dict)
print(original_dict)