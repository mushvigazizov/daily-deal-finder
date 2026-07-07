
import json
from pathlib import Path

STATE_DIR = Path("data/state")
def load_state(product_id):
    path = STATE_DIR / f"{product_id}.json"

    if not path.exists():
        return None

    return json.loads(path.read_text(encoding="utf-8"))


def is_changed(product_id, fingerprint):
    state = load_state(product_id)

    if state is None:
        return True

    return state.get("fingerprint") != fingerprint


def main():
    state = load_state("camp-001")

    if state:
        print(state)
    else:
        print("State tapilmadı")

if __name__ == "__main__":
    main()
