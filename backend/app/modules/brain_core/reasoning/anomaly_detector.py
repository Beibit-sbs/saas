from __future__ import annotations

import statistics


class AnomalyDetector:
    """Detect outliers in Brain Core metric series using z-score with IQR fallback."""

    def detect(
        self,
        *,
        tenant_id: int,
        metric_name: str,
        values: list[float],
        entity_ids: list[str] | None = None,
        z_threshold: float = 2.0,
    ) -> dict:
        if not values:
            return {
                "tenant_id": tenant_id,
                "metric_name": metric_name,
                "method": "empty",
                "baseline": {"mean": 0.0, "stddev": 0.0, "q1": None, "q3": None},
                "anomalies": [],
            }

        entity_ids = entity_ids or [f"item-{index}" for index in range(len(values))]
        if len(entity_ids) != len(values):
            raise ValueError("entity_ids_length_mismatch")

        if len(values) < 4:
            return {
                "tenant_id": tenant_id,
                "metric_name": metric_name,
                "method": "insufficient_history",
                "baseline": {
                    "mean": round(sum(values) / len(values), 4),
                    "stddev": 0.0,
                    "q1": None,
                    "q3": None,
                },
                "anomalies": [],
            }

        mean = statistics.mean(values)
        stddev = statistics.stdev(values)
        median = statistics.median(values)
        mad = statistics.median([abs(value - median) for value in values])
        min_robust_delta = max(0.1, abs(median) * 0.2)
        q1, q3 = self._quartiles(values)
        iqr = q3 - q1
        lower_iqr = q1 - 1.5 * iqr
        upper_iqr = q3 + 1.5 * iqr
        anomalies: list[dict] = []

        for index, value in enumerate(values):
            z_score = 0.0 if stddev == 0 else (value - mean) / stddev
            robust_z = 0.0 if mad == 0 else 0.6745 * (value - median) / mad
            robust_high = robust_z >= z_threshold and abs(value - median) >= min_robust_delta
            robust_low = robust_z <= -z_threshold and abs(value - median) >= min_robust_delta
            is_high = z_score >= z_threshold or robust_high or value > upper_iqr
            is_low = z_score <= -z_threshold or robust_low or value < lower_iqr
            if not is_high and not is_low:
                continue
            anomalies.append(
                {
                    "entity_id": entity_ids[index],
                    "value": value,
                    "z_score": round(z_score, 4),
                    "robust_z_score": round(robust_z, 4),
                    "direction": "high" if is_high else "low",
                    "severity": self._severity(abs(z_score), value, mean),
                    "reason": "z_score"
                    if abs(z_score) >= z_threshold
                    else ("mad" if abs(robust_z) >= z_threshold else "iqr"),
                }
            )

        anomalies.sort(key=lambda item: abs(float(item["z_score"])), reverse=True)
        return {
            "tenant_id": tenant_id,
            "metric_name": metric_name,
            "method": "z_score_iqr",
            "baseline": {
                "mean": round(mean, 4),
                "stddev": round(stddev, 4),
                "q1": round(q1, 4),
                "q3": round(q3, 4),
            },
            "anomalies": anomalies,
        }

    def _quartiles(self, values: list[float]) -> tuple[float, float]:
        ordered = sorted(values)
        midpoint = len(ordered) // 2
        lower = ordered[:midpoint]
        upper = ordered[midpoint + (0 if len(ordered) % 2 == 0 else 1) :]
        return statistics.median(lower), statistics.median(upper)

    def _severity(self, z_score: float, value: float, mean: float) -> str:
        if z_score >= 3 or abs(value - mean) >= max(1.0, mean * 0.75):
            return "critical"
        if z_score >= 2.5:
            return "high"
        return "medium"