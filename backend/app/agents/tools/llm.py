import os
import time
import re
import json
from google import genai
from google.genai import types
from app.core.config import settings

def get_gemini_client(timeout_ms: int = 15000):
    """
    Returns the initialized Gemini client if the GEMINI_API_KEY is configured.
    """
    if settings.GEMINI_API_KEY:
        return genai.Client(
            api_key=settings.GEMINI_API_KEY,
            http_options=types.HttpOptions(
                timeout=timeout_ms,
                retry_options=types.HttpRetryOptions(
                    attempts=2,  # 1 initial + 1 retry
                    initial_delay=2.0,
                    max_delay=10.0,
                    http_status_codes=[504]  # Retry specifically on 504 Gateway Timeout
                )
            )
        )
    return None

async def call_llm(system_prompt: str, user_prompt: str, mock_fallback: str = "", timeout_ms: int = 15000) -> tuple[str, str]:
    """
    Calls the configured Google Gemini LLM (gemini-2.5-flash) and returns (response_content, ai_source).
    Returns (mock_fallback, "fallback") if API credentials are not found or if the call fails.
    """
    client = get_gemini_client(timeout_ms)
    if client:
        start_time = time.time()
        try:
            config = types.GenerateContentConfig(
                system_instruction=system_prompt,
            )
            response = await client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=user_prompt,
                config=config,
            )
            elapsed = time.time() - start_time
            print(f"Gemini LLM invocation succeeded in {elapsed:.2f} seconds.")
            return response.text, "gemini"
        except Exception as e:
            elapsed = time.time() - start_time
            import traceback
            print(f"Gemini LLM invocation failed after {elapsed:.2f} seconds: {str(e)}")
            traceback.print_exc()
            
    # Clean up and return mock fallback text
    return mock_fallback, "fallback"

def extract_json_block(text: str) -> str:
    """
    Finds and extracts the first valid JSON block (object or array) from a text string.
    Supports cases where the JSON is wrapped in markdown blocks (```json ... ```) or
    preceded/followed by conversational text.
    """
    # 1. Try to find JSON markdown code blocks
    markdown_match = re.search(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL | re.IGNORECASE)
    if markdown_match:
        content = markdown_match.group(1).strip()
        try:
            json.loads(content)
            return content
        except ValueError:
            pass
            
    # 2. Find first '[' or '{' and matching closing character
    first_array = text.find('[')
    first_object = text.find('{')
    
    start_idx = -1
    end_char = ''
    
    if first_array != -1 and (first_object == -1 or first_array < first_object):
        start_idx = first_array
        end_char = ']'
    elif first_object != -1:
        start_idx = first_object
        end_char = '}'
        
    if start_idx != -1:
        # Search backwards from the end of the text for the matching closing character
        end_idx = text.rfind(end_char)
        if end_idx != -1 and end_idx > start_idx:
            candidate = text[start_idx:end_idx + 1].strip()
            try:
                json.loads(candidate)
                return candidate
            except ValueError:
                pass
                
    # 3. Bracket matching scanner fallback
    for start_char, close_char in [('[', ']'), ('{', '}')]:
        pos = text.find(start_char)
        while pos != -1:
            depth = 0
            for i in range(pos, len(text)):
                char = text[i]
                if char == start_char:
                    depth += 1
                elif char == close_char:
                    depth -= 1
                    if depth == 0:
                        candidate = text[pos:i+1].strip()
                        try:
                            json.loads(candidate)
                            return candidate
                        except ValueError:
                            pass
            pos = text.find(start_char, pos + 1)
            
    return text.strip()

