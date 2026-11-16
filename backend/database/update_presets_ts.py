from pathlib import Path

presets_path = Path("frontend/src/types/presets.ts")
if presets_path.exists():
    text = presets_path.read_text(encoding="utf-8")
    count = text.count('"middle"')
    text = text.replace('"middle"', '"bottom"')
    presets_path.write_text(text, encoding="utf-8")
    print(f"Replaced {count} instances of 'middle' with 'bottom' in {presets_path}")
