import json
from pathlib import Path

print("="*50)
print("PROPERLY FIXING JSON DATA FILE")
print("="*50)

input_file = Path('data/training_data.json')
output_file = Path('data/training_data_fixed.json')

print("\n1. Reading file content...")
with open(input_file, 'r', encoding='utf-8') as f:
    content = f.read()

print(f"   File size: {len(content)} characters")

# Split by lines and filter out empty lines
lines = [line.strip() for line in content.split('\n') if line.strip()]

print(f"   Found {len(lines)} non-empty lines")

# Parse each line as separate JSON object
data = []
valid_lines = 0
invalid_lines = 0

print("\n2. Parsing JSON objects...")
for i, line in enumerate(lines):
    try:
        obj = json.loads(line)
        data.append(obj)
        valid_lines += 1
    except json.JSONDecodeError as e:
        invalid_lines += 1
        if i < 5:  # Show first few errors
            print(f"   Invalid JSON at line {i+1}: {e}")
            print(f"   Line content: {line[:100]}...")

print(f"   Valid objects: {valid_lines}")
print(f"   Invalid objects: {invalid_lines}")

# Save as proper JSON array
print("\n3. Saving as JSON array...")
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"   Saved {len(data)} objects to {output_file}")

# Replace original
print("\n4. Replacing original file...")
import shutil
shutil.move(output_file, input_file)
print("   Original file replaced!")

print(f"\n✅ FIXED! {len(data)} training samples ready!")