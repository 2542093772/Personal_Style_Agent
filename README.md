# Personal Style Agent

A personal outfit decision agent focused on one person: profile, wardrobe, weather, occasion, style rules and feedback memory.

## MVP goals

- Maintain a personal style profile
- Maintain a wardrobe inventory
- Generate outfit recommendations from wardrobe items
- Consider temperature, rain and occasion
- Record feedback such as "显胖", "显老", "好看", "舒服"
- Use feedback to influence later recommendations

## Run

```bash
pip install -r requirements.txt
python app.py
```

The initial version is intentionally lightweight and explainable. It can later be upgraded with image understanding, product search, weather services, embeddings/vector memory and a web/mobile UI.
