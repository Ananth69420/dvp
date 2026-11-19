import json
import logging

import httpx

logger = logging.getLogger("uvicorn.error")


def generate_json(
    api_key: str,
    model: str,
    *,
    feature: str,
    system_prompt: str,
    prompt_data: dict,
    response_schema: dict,
) -> dict | None:
    if not api_key:
        return None

    model = model.removeprefix("models/")
    body = {
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": [{"text": json.dumps(prompt_data)}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseJsonSchema": response_schema,
            "maxOutputTokens": 4096,
        },
    }
    try:
        with httpx.Client(timeout=httpx.Timeout(20.0, connect=5.0)) as client:
            response = client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                headers={"x-goog-api-key": api_key},
                json=body,
            )
            response.raise_for_status()

        candidate = response.json()["candidates"][0]
        if candidate.get("finishReason") != "STOP":
            raise ValueError("Incomplete Gemini response")
        content = "".join(
            part.get("text", "")
            for part in candidate["content"]["parts"]
            if not part.get("thought")
        )
        result = json.loads(content)
        if not isinstance(result, dict):
            raise ValueError("Gemini response must be a JSON object")
        return result
    except httpx.HTTPStatusError as exc:
        logger.warning("Gemini %s returned HTTP %s. Using local rules.", feature, exc.response.status_code)
    except (httpx.RequestError, KeyError, IndexError, ValueError, TypeError, AttributeError) as exc:
        logger.warning("Gemini %s failed (%s). Using local rules.", feature, type(exc).__name__)
    return None
