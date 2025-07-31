import aiohttp
from typing import Dict, Any, List, Optional
import json
import re
import logging
import time
from .base import LLMProvider, LLMError

# Set up logging
logger = logging.getLogger(__name__)

class AnthropicError(LLMError):
    """Anthropic-specific error with additional fields."""
    def __init__(
        self,
        message: str,
        error_type: Optional[str] = None,
        status_code: Optional[int] = None,
        response_content: Optional[str] = None
    ):
        self.error_type = error_type
        super().__init__(message, status_code, response_content)
    
    def _format_error(self) -> str:
        """Format the error message with Anthropic-specific details."""
        error_parts = [f"Anthropic API Error: {self.message}"]
        if self.error_type:
            error_parts.append(f"Type: {self.error_type}")
        if self.status_code is not None:
            error_parts.append(f"Status Code: {self.status_code}")
        if self.response_content:
            try:
                # Try to parse and format JSON response
                content = json.loads(self.response_content)
                error_parts.append("Response Details:")
                error_parts.append(json.dumps(content, indent=2))
            except json.JSONDecodeError:
                # If not JSON, include raw content
                error_parts.append(f"Response Content: {self.response_content}")
        return "\n".join(error_parts)
    
detailed_model = "claude-sonnet-4-20250514"
basic_model = "claude-3-5-haiku-latest"

class Anthropic(LLMProvider):
    """Anthropic implementation of the LLM provider interface."""
    
    def __init__(self, api_key: str, basic_model: str = basic_model, detailed_model: str = detailed_model):
        """Initialize the Anthropic provider.
        
        Args:
            api_key: The Anthropic API key
            basic_model: Model to use for simple requests like updating status
            detailed_model: Model to use for requests needing more detail, like action descriptions
        """
        self.api_key = api_key
        self.basic_model = basic_model
        self.detailed_model = detailed_model
        self.endpoint = "https://api.anthropic.com/v1/messages"
        self.headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        }

    async def _handle_response(self, response: aiohttp.ClientResponse, response_text: str) -> Dict[str, Any]:
        """Handle the API response, extracting error details if present.
        
        Args:
            response: The response from the Anthropic API.
            response_text: The response text content.
            
        Returns:
            The parsed JSON response.
            
        Raises:
            AnthropicError: If the response contains an error, with details from the error payload.
            LLMError: For other types of errors.
        """
        try:
            content = json.loads(response_text)
        except json.JSONDecodeError:
            # If we can't parse JSON, raise a generic error
            raise LLMError(
                f"Invalid response from Anthropic API: {response_text}",
                status_code=response.status,
                response_content=response_text
            )
        
        # Check for error in response
        if "error" in content:
            error = content["error"]
            raise AnthropicError(
                message=error.get("message", "Unknown error"),
                error_type=error.get("type"),
                status_code=response.status,
                response_content=response_text
            )
        
        # If no error but status code indicates failure, raise generic error
        if not response.ok:
            raise LLMError(
                f"Anthropic API request failed: {response_text}",
                status_code=response.status,
                response_content=response_text
            )
        
        return content

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract and parse JSON from a string that may contain extra characters.
        
        This function looks for JSON content in a string, even if it's surrounded by
        other text (like markdown code blocks or explanatory text). It will:
        1. Try to parse the entire string as JSON first
        2. Look for JSON-like content between curly braces
        3. Look for JSON-like content in markdown code blocks
        
        Args:
            text: The string that may contain JSON
            
        Returns:
            The parsed JSON as a dictionary
            
        Raises:
            AnthropicError: If no valid JSON can be found in the string
        """
        # First try parsing the entire string
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
            
        # Look for content between curly braces
        json_pattern = r'\{[^{}]*\}'
        matches = re.finditer(json_pattern, text)
        for match in matches:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                continue
                
        # Look for JSON in markdown code blocks
        code_block_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
        matches = re.finditer(code_block_pattern, text, re.DOTALL)
        for match in matches:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                continue
                
        raise AnthropicError(
            "No valid JSON found in response",
            response_content=text
        )

    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 10000,
        **kwargs
    ) -> Dict[str, Any]:
        """Get a chat completion from Anthropic.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            temperature: Controls randomness (0.0 to 1.0)
            max_tokens: Maximum number of tokens to generate
            **kwargs: Additional Anthropic specific arguments
            
        Returns:
            Dictionary containing the Anthropic response
            
        Raises:
            AnthropicError: If the API returns an error
            LLMError: For other types of errors
        """
        start_time = time.time()
        try:
            # Convert messages to Anthropic format
            anthropic_messages = []
            for msg in messages:
                # Anthropic uses 'user' and 'assistant' roles
                role = "user" if msg["role"] == "user" else "assistant"
                anthropic_messages.append({
                    "role": role,
                    "content": msg["content"]
                })

            payload = {
                "model": self.basic_model,
                "messages": anthropic_messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                **kwargs
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(self.endpoint, headers=self.headers, json=payload) as response:
                    response_text = await response.text()
                    content = await self._handle_response(response, response_text)
                    result = content.get("content", [{}])[0].get("text", "")
            
            duration = time.time() - start_time
            logger.info(f"Anthropic chat_completion request completed in {duration:.2f} seconds")
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Anthropic chat_completion request failed after {duration:.2f} seconds: {str(e)}")
            raise

    async def structured_completion(
        self,
        messages: List[Dict[str, Any]],
        schema: Dict[str, Any],
        name: str = "structure",
        temperature: float = 0.7,
        max_tokens: int = 10000,
        use_detailed_model: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """Get a structured (JSON) completion from Anthropic."""
        start_time = time.time()
        try:
            # Wrap the input schema in a tool
            tool = {
                "name": name,
                "description": "Return data in a strict JSON format",
                "input_schema": schema
            }

            # Separate system messages from conversation messages
            system_content = ""
            conversation_messages = []
            
            for msg in messages:
                if msg["role"] == "system":
                    system_content += msg["content"] + "\n"
                else:
                    conversation_messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
            
            # Add JSON schema instruction to system prompt
            json_instruction = f"""
                IMPORTANT: You must respond with a complete JSON object that includes ALL fields from this schema. Do not omit any fields.

                Required JSON Schema:
                {json.dumps(schema, indent=2)}

                Your response must be valid JSON that includes every single property defined in the schema above. Include all nested objects, arrays, and properties."""
            system_content += json_instruction
            
            payload = {
                "model": self.detailed_model if use_detailed_model else self.basic_model,
                "messages": conversation_messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "tool_choice": {
                    "type": "tool",
                    "name": name
                },
                "tools": [tool],
                **kwargs
            }
            
            # Add system parameter if we have system content
            if system_content.strip():
                payload["system"] = system_content.strip()
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.endpoint, headers=self.headers, json=payload) as response:
                    response_text = await response.text()
                    content = await self._handle_response(response, response_text)
            
            try:
                if not content.get("content"):
                    raise AnthropicError("No content in response", response_content=json.dumps(content))
                
                first_reply = content["content"][0]
                response_type = first_reply.get("type")
                if not response_type or response_type != "tool_use":
                    raise AnthropicError("Content does not specify tool_use", response_content=json.dumps(content))
                input = first_reply.get("input")
                if not input:
                    raise AnthropicError("Content does not include structured data input", response_content=json.dumps(content))
                
                duration = time.time() - start_time
                logger.info(f"Anthropic structured_completion request completed in {duration:.2f} seconds")
                return input
                
            except (KeyError, IndexError) as e:
                raise AnthropicError(
                    f"Failed to parse Anthropic response: {e}",
                    response_content=json.dumps(content)
                )
                
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Anthropic structured_completion request failed after {duration:.2f} seconds: {str(e)}")
            raise