#!/usr/bin/env python3
"""
Performance Optimization Script
Adds performance-enhancing decorators to critical functions in the app.
"""

import os
import re

# Helper function to add a decorator to a function definition
def add_decorator_to_file(file_path, decorator_pattern, function_pattern):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return False
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Use regex to find function definitions and add decorator if not present
    pattern = re.compile(f"(^|\n)(?!{decorator_pattern})(    )?{function_pattern}", re.MULTILINE)
    modified_content = pattern.sub(f"\\1{decorator_pattern}\\2{function_pattern}", content)
    
    if content != modified_content:
        with open(file_path, 'w') as f:
            f.write(modified_content)
        return True
    return False

# Simpler optimization approach
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

# Add import and caching decorator to agent.py
with open('utils/agent.py', 'r') as f:
    content = f.read()

if 'import functools' not in content:
    content = content.replace('import ', 'import functools\nimport ', 1)

if '@functools.lru_cache(maxsize=32)' not in content:
    content = content.replace('    def get_specific_bet_recommendations', '    @functools.lru_cache(maxsize=32)\n    def get_specific_bet_recommendations', 1)

with open('utils/agent.py', 'w') as f:
    f.write(content)

# Add caching to analysis.py
with open('utils/analysis.py', 'r') as f:
    content = f.read()

if 'import functools' not in content:
    content = content.replace('import ', 'import functools\nimport ', 1)

if '@functools.lru_cache(maxsize=16)' not in content:
    content = content.replace('    def get_hot_cold_numbers', '    @functools.lru_cache(maxsize=16)\n    def get_hot_cold_numbers', 1)

with open('utils/analysis.py', 'w') as f:
    f.write(content)

print("Added decorators to visualization_optimized.py")
print("Added functools import and caching to agent.py")
print("Added functools import and caching to analysis.py")

print("Performance optimization complete")
