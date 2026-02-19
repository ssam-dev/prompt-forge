import asyncio
import json
import re
from typing import Any

import litellm

try:
    from litellm import RateLimitError
except Exception:  # pragma: no cover - fallback if class is unavailable
    class RateLimitError(Exception):
        pass


def _normalize_groq_model(model: str) -> str:
    model_name = model.strip()
    if model_name.startswith("groq/"):
        return model_name
    return f"groq/{model_name}"


async def safe_completion(**kwargs):
    last_error: Exception | None = None
    for attempt in range(4):
        try:
            return await litellm.acompletion(**kwargs)
        except RateLimitError as exc:
            last_error = exc
            wait_seconds = 15 * (2**attempt)
            print(f"Rate limit hit — retry {attempt + 1}/4 in {wait_seconds}s")
            await asyncio.sleep(wait_seconds)
            continue
        except Exception as exc:
            message = str(exc).lower()
            is_rate_limited = "429" in message or ("rate" in message and "limit" in message)
            if is_rate_limited and attempt < 3:
                last_error = exc
                wait_seconds = 15 * (2**attempt)
                print(f"Rate limit (429) hit — retry {attempt + 1}/4 in {wait_seconds}s")
                await asyncio.sleep(wait_seconds)
                continue
            raise

    raise RuntimeError("Rate limit retries exhausted") from last_error


def _extract_json_object(raw_text: str) -> str:
    text = raw_text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    text = text.strip()

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start : end + 1]

    text = re.sub(r",\s*([}\]])", r"\1", text)
    return text


def _safe_json_parse(raw_text: str) -> dict[str, Any] | None:
    cleaned = _extract_json_object(raw_text)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e} — cleaned snippet: {cleaned[:200]}...")
        pass

    try:
        return json.loads(cleaned.replace("'", '"'))
    except json.JSONDecodeError as e:
        print(f"JSON parse fallback failed: {e}")
        return None


CODING_SYSTEM = (
    "You are a world-class coding agent prompt engineer. Optimize for clarity, "
    "step-by-step reasoning, strict JSON/YAML output, tool calls if needed, "
    "error handling, acceptance criteria."
)

RESEARCH_SYSTEM = (
    "You are an expert AI research prompt optimizer. Include hypothesis, "
    "variables/definitions, methodology, reproducibility notes, expected analysis, "
    "success metrics."
)

CONCISE_SYSTEM = (
    "Make the shortest possible effective version of this prompt while preserving "
    "100% intent. Remove fluff, combine ideas."
)

STRUCTURED_SYSTEM = (
    "Force perfect structure: ROLE + CLEAR TASK + STEP-BY-STEP INSTRUCTIONS + "
    "OUTPUT FORMAT + CONSTRAINTS + 1-2 EXAMPLES."
)


def estimate_tokens(text: str) -> int:
    """
    Roughly estimate token count from text length.
    Approximation: words + chars/4 (consistent with typical tokenizers).
    """
    return len(text.split()) + len(text) // 4


async def _optimize_prompt(
    raw_prompt: str, system_prompt: str, model: str, api_key: str
) -> str:
    """
    Helper to call the Groq model via litellm and return the optimized prompt text.
    Returns an error string if the call fails.
    """
    try:
        response = await safe_completion(
            model=_normalize_groq_model(model),
            api_key=api_key,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": raw_prompt},
            ],
        )
        return response.choices[0].message["content"]  # type: ignore[index]
    except Exception as e:
        return f"Error: {e}"


async def run_optimizers(
    raw_prompt: str, mode: str, model: str, api_key: str
) -> dict[str, str]:
    """
    Run four optimizer variants in parallel using Groq via litellm.
    Returns a dict mapping optimization type to optimized prompt (or error string).
    """
    # `mode` is currently unused but kept for future expansion / API stability
    _ = mode

    try:
        coding_task = _optimize_prompt(raw_prompt, CODING_SYSTEM, model, api_key)
        research_task = _optimize_prompt(raw_prompt, RESEARCH_SYSTEM, model, api_key)
        coding, research = await asyncio.gather(coding_task, research_task)
        await asyncio.sleep(2)

        concise_task = _optimize_prompt(raw_prompt, CONCISE_SYSTEM, model, api_key)
        structured_task = _optimize_prompt(raw_prompt, STRUCTURED_SYSTEM, model, api_key)
        concise, structured = await asyncio.gather(concise_task, structured_task)
        await asyncio.sleep(2)

        return {
            "Coding": coding,
            "Research": research,
            "Concise": concise,
            "Structured": structured,
        }
    except Exception as e:
        # Fallback if something unexpected happens outside individual calls
        error_msg = f"Error: {e}"
        return {
            "Coding": error_msg,
            "Research": error_msg,
            "Concise": error_msg,
            "Structured": error_msg,
        }


async def get_winner_and_scores(
    results: dict[str, str], mode: str, model: str, api_key: str
) -> tuple[str, dict[str, int]]:
    """
    Use a Groq model via litellm to judge the provided optimized prompts.
    Returns the winner name and a dict of scores per variant.
    """
    variant_names = list(results.keys())
    default_scores = {name: 6 for name in variant_names}

    judge_system = (
        "You are a prompt quality judge. "
        f"Score each variant 1-10 on: clarity, specificity for {mode}, "
        "token efficiency, expected performance. "
        "Respond with ONLY valid JSON and no markdown/code fences. "
        "Use this exact schema with double quotes: "
        "{\"scores\": {\"Coding\": 9, \"Research\": 8, \"Concise\": 7, \"Structured\": 8}, "
        "\"winner\": \"Coding\", \"reason\": \"brief explanation\"}."
    )

    # Provide the variants in a structured way to the judge
    user_content = json.dumps(
        {
            "instructions": "Judge the following prompt variants and pick a single best winner.",
            "variants": results,
        },
        ensure_ascii=False,
        indent=2,
    )

    try:
        response = await safe_completion(
            model=_normalize_groq_model(model),
            api_key=api_key,
            messages=[
                {"role": "system", "content": judge_system},
                {"role": "user", "content": user_content},
            ],
        )
        content = response.choices[0].message["content"]  # type: ignore[index]

        content_str = content if isinstance(content, str) else str(content)
        parsed = _safe_json_parse(content_str)

        if not isinstance(parsed, dict):
            fallback_winner = variant_names[0] if variant_names else "Unknown"
            return fallback_winner, default_scores

        scores_raw = parsed.get("scores", {}) if isinstance(parsed, dict) else {}
        winner = parsed.get("winner") if isinstance(parsed, dict) else None

        # Normalize scores to int dict[str, int]
        scores: dict[str, int] = {}
        if isinstance(scores_raw, dict):
            for name, value in scores_raw.items():
                try:
                    scores[name] = int(value)
                except (TypeError, ValueError):
                    continue

        for name in variant_names:
            if name not in scores:
                scores[name] = default_scores[name]

        if not isinstance(winner, str) or winner not in results:
            winner = max(scores.items(), key=lambda kv: kv[1])[0] if scores else "Unknown"

        return winner, scores

    except Exception as e:
        fallback_winner = variant_names[0] if variant_names else f"Error: {e}"
        return fallback_winner, default_scores


async def get_fusion(
    results: dict[str, str], model: str, api_key: str
) -> str:
    """
    Combine the best parts of the four optimized prompts into one fused version.
    """
    # Build the user prompt with all four variants separated by ---
    parts = []
    for name, text in results.items():
        parts.append(f"### {name} Variant\n{text}")
    joined = "\n\n---\n\n".join(parts)

    user_prompt = (
        "Combine the best parts of these 4 optimized prompts into one ultimate, "
        "balanced version: [paste all 4 separated by ---]\n\n"
        f"{joined}"
    )

    try:
        response = await safe_completion(
            model=_normalize_groq_model(model),
            api_key=api_key,
            messages=[
                {
                    "role": "user",
                    "content": user_prompt,
                }
            ],
        )
        content = response.choices[0].message["content"]  # type: ignore[index]
        # Ensure we return a plain string
        return content if isinstance(content, str) else str(content)
    except Exception as e:
        return f"Error: {e}"

