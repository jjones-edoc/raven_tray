import os
from openai import OpenAI


def perplexity_search(query: str, model_name="llama-3.1-sonar-large-128k-online", api_key=None, base_url="https://api.perplexity.ai"):
    key = os.getenv("PERPLEXITY_API_KEY")

    client = OpenAI(api_key=key, base_url=base_url)

    messages = [
        {
            "role": "user",
            "content": (
                query
            ),
        },
    ]

    response = client.chat.completions.create(
        model=model_name,
        messages=messages,  # type: ignore
    )
    result = response.choices[0].message.content  # only the text is returned
    return result
