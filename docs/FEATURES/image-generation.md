# Feature: Rasm Generatsiya

## Maqsad

User prompt (va optional reference) orqali rasm(lar) olish. Model tanlash va narxlash token asosida.

## Input

- `prompt` (required, max length policy)
- `model_key` (default yoki user tanlaydi)
- `n_outputs` (1..k)
- `advanced_settings` (optional)

## Output

- 1..N ta generated image
- job status va metadata (seed, provider id, cost)

## Token narxlash

Narx formulasi (draft):
- `base_cost(model)` + `quality_multiplier(steps/size)` + `ref_multiplier(ref_count)`

Qoida:
- “Generate” bosilganda token **hold** qilinadi.
- Job `succeeded` → hold finalize.
- Job `failed/canceled` → refund.

## Failure handling

Common error categories:
- provider timeout
- content policy block
- invalid reference image
- insufficient balance

UX:
- userga tushunarli error + “Try again”/“Change settings”.

