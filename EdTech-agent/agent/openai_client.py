"""
Shared OpenAI client.
SSL verification can be disabled via DISABLE_SSL_VERIFY=1 (for corporate proxies).
"""
import httpx
from openai import OpenAI
from config import OPENAI_API_KEY, DISABLE_SSL_VERIFY

if DISABLE_SSL_VERIFY:
    _http_client = httpx.Client(verify=False)
    client = OpenAI(api_key=OPENAI_API_KEY, http_client=_http_client)
else:
    client = OpenAI(api_key=OPENAI_API_KEY)
