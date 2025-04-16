#!/usr/bin/env python3

with open('utils/visualization_optimized.py', 'r') as f:
    lines = f.readlines()

output_lines = []
for line in lines:
    if line.strip().startswith('def plot_') and not line.strip().startswith('@with_clean_dataframe'):
        if 'spins_df' in line:
            # Add decorator to methods that take spins_df
            output_lines.append('    @with_clean_dataframe\n')
        output_lines.append(line)
    else:
        output_lines.append(line)

with open('utils/visualization_optimized.py', 'w') as f:
    f.writelines(output_lines)

print("Added decorators to visualization_optimized.py")
