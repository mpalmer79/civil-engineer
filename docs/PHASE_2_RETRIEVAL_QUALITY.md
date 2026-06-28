# Phase 2 Retrieval Quality Report

Measured over a small labeled query set against real-derived chunk evidence. Scores are relevance measurements for comparing retrieval modes, not statements about document content.

| Mode | Recall@5 | Precision@5 | MRR |
| --- | --- | --- | --- |
| keyword | 0.667 | 0.133 | 0.667 |
| semantic | 1.0 | 0.2 | 1.0 |
| hybrid | 1.0 | 0.2 | 1.0 |

## keyword per-query

| Query | Recall@5 | Precision@5 | RR |
| --- | --- | --- | --- |
| exact: detention basin outlet | 1.0 | 0.2 | 1.0 |
| semantic: retention pond | 0.0 | 0.0 | 0.0 |
| exact: infiltration drawdown | 1.0 | 0.2 | 1.0 |
| semantic: groundwater recharge | 0.0 | 0.0 | 0.0 |
| exact: silt fence erosion | 1.0 | 0.2 | 1.0 |
| exact: culvert capacity | 1.0 | 0.2 | 1.0 |

## semantic per-query

| Query | Recall@5 | Precision@5 | RR |
| --- | --- | --- | --- |
| exact: detention basin outlet | 1.0 | 0.2 | 1.0 |
| semantic: retention pond | 1.0 | 0.2 | 1.0 |
| exact: infiltration drawdown | 1.0 | 0.2 | 1.0 |
| semantic: groundwater recharge | 1.0 | 0.2 | 1.0 |
| exact: silt fence erosion | 1.0 | 0.2 | 1.0 |
| exact: culvert capacity | 1.0 | 0.2 | 1.0 |

## hybrid per-query

| Query | Recall@5 | Precision@5 | RR |
| --- | --- | --- | --- |
| exact: detention basin outlet | 1.0 | 0.2 | 1.0 |
| semantic: retention pond | 1.0 | 0.2 | 1.0 |
| exact: infiltration drawdown | 1.0 | 0.2 | 1.0 |
| semantic: groundwater recharge | 1.0 | 0.2 | 1.0 |
| exact: silt fence erosion | 1.0 | 0.2 | 1.0 |
| exact: culvert capacity | 1.0 | 0.2 | 1.0 |

