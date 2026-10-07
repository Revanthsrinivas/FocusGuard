import chardet
import json
from pathlib import Path

print("="*50)
print("FIXING JSON DATA FILE")
print("="*50)

input_file = Path('data/training_data.json')

# Step 1: Detect encoding
print("\n1. Detecting file encoding...")
with open(input_file, 'rb') as f:
    raw = f.read()
    result = chardet.detect(raw)
    print(f"   Detected encoding: {result['encoding']}")
    print(f"   Confidence: {result['confidence']}")

# Step 2: Try to load with detected encoding
print("\n2. Loading data...")
try:
    with open(input_file, 'r', encoding=result['encoding']) as f:
        data = json.load(f)
    print(f"   Successfully loaded {len(data)} samples")
except Exception as e:
    print(f"   Failed with {result['encoding']}: {e}")
    print("   Trying utf-8...")
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"   Successfully loaded {len(data)} samples with utf-8")
        except Exception as e:
            print(f"   Error with utf-8: {e}")
output_file = Path('data/training_data_clean.json')
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
print(f"   Saved to {output_file}")

# Step 4: Replace original
print("\n4. Replacing original file...")
import shutil
shutil.move(output_file, input_file)
print("   Original file replaced!")

print("\n✅ DATA FILE FIXED!")