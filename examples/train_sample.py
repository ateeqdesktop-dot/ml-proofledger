from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def train_centroids(rows: list[dict[str, str]]) -> dict[str, tuple[float, float]]:
    grouped: dict[str, list[tuple[float, float]]] = {}
    for row in rows:
        grouped.setdefault(row["label"], []).append((float(row["x1"]), float(row["x2"])))
    return {
        label: (
            sum(point[0] for point in points) / len(points),
            sum(point[1] for point in points) / len(points),
        )
        for label, points in sorted(grouped.items())
    }


def predict(centroids: dict[str, tuple[float, float]], row: dict[str, str]) -> str:
    point = (float(row["x1"]), float(row["x2"]))
    return min(
        centroids,
        key=lambda label: math.dist(point, centroids[label]),
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Train a deterministic nearest-centroid fixture model."
    )
    parser.add_argument("--data", type=Path, default=Path(__file__).with_name("dataset.csv"))
    parser.add_argument("--model", type=Path, default=Path(__file__).with_name("model.json"))
    parser.add_argument(
        "--predictions",
        type=Path,
        default=Path(__file__).with_name("predictions.csv"),
    )
    args = parser.parse_args()

    rows = read_rows(args.data)
    train_rows = [row for row in rows if row["split"] == "train"]
    test_rows = [row for row in rows if row["split"] == "test"]
    centroids = train_centroids(train_rows)
    predictions = [predict(centroids, row) for row in test_rows]
    correct = sum(
        prediction == row["label"] for prediction, row in zip(predictions, test_rows, strict=True)
    )
    accuracy = correct / len(test_rows) if test_rows else 0.0

    args.model.write_text(
        json.dumps(
            {"algorithm": "nearest_centroid", "features": ["x1", "x2"], "centroids": centroids},
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    with args.predictions.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["x1", "x2", "label", "prediction"])
        writer.writeheader()
        for row, prediction in zip(test_rows, predictions, strict=True):
            writer.writerow(
                {"x1": row["x1"], "x2": row["x2"], "label": row["label"], "prediction": prediction}
            )
    print(
        json.dumps(
            {"accuracy": accuracy, "train_rows": len(train_rows), "test_rows": len(test_rows)}
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
