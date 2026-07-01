# Scoring

The MVP uses a conservative keyword score before calling DeepSeek. Papers below `RULE_FILTER_THRESHOLD` are stored in SQLite but not summarized.

## Positive Keywords

| Keyword | Score |
| --- | ---: |
| rendering | 3 |
| real-time rendering | 6 |
| real time rendering | 6 |
| path tracing | 6 |
| ray tracing | 6 |
| global illumination | 6 |
| radiance cache | 6 |
| reservoir | 5 |
| restir | 8 |
| rtxdi | 7 |
| denoising | 5 |
| neural rendering | 5 |
| gaussian splatting | 4 |
| brdf | 4 |
| bsdf | 4 |
| material | 3 |
| shader | 5 |
| mesh shader | 6 |
| work graph | 5 |
| vulkan | 6 |
| directx | 5 |
| directx 12 | 6 |
| unreal engine | 6 |
| ue5 | 6 |
| ue 5 | 6 |
| unreal | 4 |
| mega lights | 6 |
| path tracer | 5 |
| hardware ray tracing | 6 |
| virtual shadow map | 5 |
| virtualized geometry | 4 |
| lumen | 5 |
| nanite | 5 |
| rtx | 4 |
| dlss | 5 |
| ray reconstruction | 5 |
| opacity micromap | 5 |
| neural radiance cache | 6 |
| fsr | 5 |

## Negative Keywords

| Keyword | Score |
| --- | ---: |
| medical | -6 |
| ct | -5 |
| mri | -5 |
| remote sensing | -5 |
| satellite | -4 |
| protein | -7 |
| language model | -4 |
| llm | -3 |
| document | -4 |
| ocr | -4 |

## LLM Relevance Schema

DeepSeek validates:

- graphics related
- rendering related
- main category
- sub tags
- technical keywords
- novelty score from 1 to 5
- job relevance score from 1 to 5
- read priority
- reason
- uncertainty

## Read Priority

- `must_read`: high relevance to rendering engineering or game engine learning
- `read_later`: useful but less urgent
- `archive_only`: stored but not pushed
- `skip`: ignored after classification
