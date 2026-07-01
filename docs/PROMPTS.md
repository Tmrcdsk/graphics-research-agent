# Prompts

## Prompt Versioning

Prompt versions are code constants and must be changed whenever required fields, instructions, or behavior change.

Current versions:

- `classification_v2`
- `summary_v2`

Do not silently change prompt schemas. Update tests and this document when prompts change.

## Classification Prompt

The classification prompt is implemented in `app/llm/prompts.py` as `build_classification_prompt`.

It asks DeepSeek to act as a critical technical assistant for computer graphics research items, including arXiv papers and official rendering-related website posts. It applies the user's real-time rendering profile, avoids noisy generic AI/medical/remote-sensing recommendations, and returns JSON only.

Required fields:

```json
{
  "is_graphics_related": true,
  "is_rendering_related": true,
  "main_category": "string",
  "sub_tags": ["string"],
  "technical_keywords": ["string"],
  "novelty_score": 1,
  "job_relevance_score": 1,
  "read_priority": "must_read",
  "reason": "string",
  "uncertainty": "string"
}
```

## Summarization Prompt

The summary prompt is implemented in `app/llm/prompts.py` as `build_summary_prompt`.

It asks for a Chinese summary based only on title and abstract/excerpt, keeping technical terms such as ReSTIR, path tracing, BRDF, Vulkan, UE, shader, and GPU in English when appropriate.

Required fields:

```json
{
  "title_zh": "string",
  "one_sentence": "string",
  "problem": "string",
  "method": "string",
  "relation_to_user_goal": "string",
  "likely_usefulness": "string",
  "uncertainty": "string",
  "read_priority": "must_read",
  "job_relevance_score": 1,
  "novelty_score": 1
}
```

## Good Summary

A good summary is conservative, Chinese, specific to the abstract, and clear about uncertainty.

## Bad Summary

A bad summary claims code availability, benchmarks, production usability, or engine integration unless the metadata explicitly says so.
