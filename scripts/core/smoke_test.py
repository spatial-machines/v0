from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt


BASE = Path(__file__).resolve().parents[2]
OUT = BASE / "outputs" / "charts"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)

    # Simple runtime smoke test
    df = pd.DataFrame({
        "category": ["a", "b", "c"],
        "value": [1, 3, 2],
    })

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(df["category"], df["value"])
    ax.set_title("GIS Agent Smoke Test")
    ax.set_xlabel("category")
    ax.set_ylabel("value")
    fig.tight_layout()

    out_file = OUT / "smoke-test-chart.png"
    fig.savefig(out_file, dpi=150)
    print(f"wrote {out_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
