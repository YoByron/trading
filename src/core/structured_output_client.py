import json
import logging
from typing import TypeVar

from openai import AsyncOpenAI, OpenAI
from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)
logger = logging.getLogger(__name__)


class StructuredOutputError(Exception):
    """Raised when structured output parsing fails after retries."""

    pass


class StructuredLLMClient:
    """
    A wrapper around OpenAI clients to enforce Pydantic schema validation.
    Supports both native 'beta.parse' (Structured Outputs) and standard JSON mode with validation.
    """

    def __init__(self, client: OpenAI | AsyncOpenAI, model: str):
        self.client = client
        self.model = model
        self.is_async = isinstance(client, AsyncOpenAI)

    def _get_schema_prompt(self, pydantic_model: type[BaseModel]) -> str:
        """Generate a system prompt snippet enforcing the JSON schema."""
        schema = pydantic_model.model_json_schema()
        return (
            f"\nYou must output strictly valid JSON matching the following schema:\n"
            f"{json.dumps(schema, indent=2)}\n"
            f"Do not include markdown formatting (```json) or prose. Just the JSON object."
        )

    async def generate_async(
        self,
        prompt: str,
        response_model: type[T],
        system_prompt: str = "You are a helpful assistant.",
        temperature: float = 0.0,
        max_retries: int = 3,
    ) -> T:
        """
        Generate structured output asynchronously.

        Tries to use native Structured Outputs (tool/json_schema) if supported by provider,
        otherwise falls back to JSON mode + Validation.
        """
        # For OpenRouter, 'beta.parse' behavior can be inconsistent across providers.
        # We will use standard chat completions with JSON mode and unconditional Pydantic validation.

        full_system_prompt = f"{system_prompt}{self._get_schema_prompt(response_model)}"

        messages = [
            {"role": "system", "content": full_system_prompt},
            {"role": "user", "content": prompt},
        ]

        for attempt in range(max_retries):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    response_format={"type": "json_object"},
                )

                content = response.choices[0].message.content
                if not content:
                    raise StructuredOutputError("Empty response from LLM")

                # cleaner extraction if markdown is present
                clean_content = self._clean_json_string(content)

                data = json.loads(clean_content)
                return response_model.model_validate(data)

            except (ValidationError, json.JSONDecodeError) as e:
                logger.warning(f"Attempt {attempt + 1} failed validation: {e}")
                if attempt == max_retries - 1:
                    raise StructuredOutputError(
                        f"Failed to validate response after {max_retries} attempts: {e}"
                    )
            except Exception as e:
                logger.error(f"LLM call failed: {e}")
                raise

    def generate_sync(
        self,
        prompt: str,
        response_model: type[T],
        system_prompt: str = "You are a helpful assistant.",
        temperature: float = 0.0,
        max_retries: int = 3,
    ) -> T:
        """Synchronous version."""
        if self.is_async:
            raise RuntimeError("Cannot use generate_sync with AsyncOpenAI client")

        full_system_prompt = f"{system_prompt}{self._get_schema_prompt(response_model)}"

        messages = [
            {"role": "system", "content": full_system_prompt},
            {"role": "user", "content": prompt},
        ]

        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    response_format={"type": "json_object"},
                )

                content = response.choices[0].message.content
                if not content:
                    raise StructuredOutputError("Empty response from LLM")

                clean_content = self._clean_json_string(content)

                data = json.loads(clean_content)
                return response_model.model_validate(data)

            except (ValidationError, json.JSONDecodeError) as e:
                logger.warning(f"Attempt {attempt + 1} failed validation: {e}")
                if attempt == max_retries - 1:
                    raise StructuredOutputError(
                        f"Failed to validate response after {max_retries} attempts: {e}"
                    )
            except Exception as e:
                logger.error(f"LLM call failed: {e}")
                raise

    @staticmethod
    def _clean_json_string(content: str) -> str:
        """Remove markdown constraints like ```json ... ```"""
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        return content.strip()
