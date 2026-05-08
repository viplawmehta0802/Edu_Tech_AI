"""
Shared OpenAI client.
SSL verification can be disabled via DISABLE_SSL_VERIFY=1 (for corporate proxies).
"""
import httpx
from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_API_BASE, DISABLE_SSL_VERIFY

client_kwargs = {
    "api_key": OPENAI_API_KEY,
}
if OPENAI_API_BASE:
    client_kwargs["base_url"] = OPENAI_API_BASE
elif OPENAI_API_KEY.startswith("sk-or-"):
    client_kwargs["base_url"] = "https://openrouter.ai/api/v1"

if DISABLE_SSL_VERIFY:
    _http_client = httpx.Client(verify=False)
    client = OpenAI(http_client=_http_client, **client_kwargs)
else:
    client = OpenAI(**client_kwargs)
