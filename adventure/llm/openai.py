from typing import Dict, Any, List, Optional, Union, cast, NoReturn, Sequence, TypedDict, Any
from .base import LLMProvider, LLMError
import json
import re
from openai import OpenAI as OpenAIClient
from openai.types.chat import (
    ChatCompletionMessage,
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
    ChatCompletionAssistantMessageParam,
)
from openai.types.chat.chat_completion import ChatCompletion
from openai.types.chat.completion_create_params import ResponseFormat

class ResponseInputItem(TypedDict):
    role: str
    content: str

ResponseInputParam = Sequence[ResponseInputItem]

def extract_json(content: str) -> Dict[str, Any]:
    """Extract and parse JSON from a string that may contain other text.
    
    Args:
        content: A string that may contain JSON embedded within it.
        
    Returns:
        The parsed JSON as a dictionary.
        
    Raises:
        json.JSONDecodeError: If no valid JSON is found or if the JSON is malformed.
    """
    # Find the first occurrence of either { or [ that starts a JSON object/array
    match = re.search(r'(\{.*\}|\[.*\])', content, re.DOTALL)
    if not match:
        raise json.JSONDecodeError("No JSON object or array found in content", content, 0)
    
    json_str = match.group(1)
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        # If the first match isn't valid JSON, try to find a more precise match
        # This handles cases where the regex might match too much
        stack = []
        start_idx = None
        for i, char in enumerate(content):
            if char in '{[':
                if not stack:  # This is the start of our JSON
                    start_idx = i
                stack.append(char)
            elif char in '}]':
                if not stack:  # Unmatched closing bracket
                    continue
                if (char == '}' and stack[-1] == '{') or (char == ']' and stack[-1] == '['):
                    stack.pop()
                    if not stack and start_idx is not None:  # We found a complete JSON object/array
                        try:
                            return json.loads(content[start_idx:i+1])
                        except json.JSONDecodeError:
                            continue
        raise json.JSONDecodeError("No valid JSON found in content", content, 0)

class OpenAIError(LLMError):
    """OpenAI-specific error with additional fields."""
    def __init__(
        self,
        message: str,
        error_type: Optional[str] = None,
        param: Optional[str] = None,
        code: Optional[str] = None,
        status_code: Optional[int] = None,
        response_content: Optional[str] = None
    ):
        self.error_type = error_type
        self.param = param
        self.code = code
        super().__init__(message, status_code, response_content)
    
    def _format_error(self) -> str:
        """Format the error message with OpenAI-specific details."""
        error_parts = [f"OpenAI API Error: {self.message}"]
        if self.error_type:
            error_parts.append(f"Type: {self.error_type}")
        if self.param:
            error_parts.append(f"Parameter: {self.param}")
        if self.code:
            error_parts.append(f"Code: {self.code}")
        if self.status_code is not None:
            error_parts.append(f"Status Code: {self.status_code}")
        return "\n".join(error_parts)

class OpenAI(LLMProvider):
    """OpenAI API provider implementation using the official Python SDK."""
    
    def __init__(self, api_key: str, basic_model: str = "gpt-4.1-mini", detailed_model: str = "gpt-4.1"):
        """Initialize the OpenAI provider.
        
        Args:
            api_key: The OpenAI API key.
            basic_model: The model to use for basic completions.
            detailed_model: The model to use for detailed completions.
        """
        self.client = OpenAIClient(api_key=api_key)
        self.basic_model = basic_model
        self.detailed_model = detailed_model
    
    def _handle_error(self, error: Exception) -> NoReturn:
        """Handle OpenAI SDK errors and convert them to our error types.
        
        Args:
            error: The error from the OpenAI SDK.
            
        Raises:
            OpenAIError: If the error is from the OpenAI API.
            LLMError: For other types of errors.
        """
        from openai import APIError, APIConnectionError, APITimeoutError, RateLimitError
        
        if isinstance(error, APIError):
            # Extract error details from the API error
            error_dict = getattr(error, 'body', {}) or {}
            if isinstance(error_dict, dict):
                raise OpenAIError(
                    message=str(error),
                    error_type=error_dict.get('type'),
                    param=error_dict.get('param'),
                    code=error_dict.get('code'),
                    status_code=getattr(error, 'status_code', None),
                    response_content=str(error_dict)
                )
            else:
                raise OpenAIError(str(error))
        elif isinstance(error, (APIConnectionError, APITimeoutError)):
            raise LLMError(f"Connection error: {str(error)}")
        elif isinstance(error, RateLimitError):
            raise LLMError(f"Rate limit exceeded: {str(error)}")
        else:
            raise LLMError(f"Unexpected error: {str(error)}")
    
    def _convert_messages(self, messages: List[Dict[str, str]]) -> List[ChatCompletionMessageParam]:
        """Convert our message format to OpenAI SDK message format.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'.
            
        Returns:
            List of properly typed message parameters for the OpenAI SDK.
        """
        converted_messages: List[ChatCompletionMessageParam] = []
        for msg in messages:
            role = msg.get('role', '')
            content = msg.get('content', '')
            
            if role == 'system':
                converted_messages.append(ChatCompletionSystemMessageParam(role='system', content=content))
            elif role == 'user':
                converted_messages.append(ChatCompletionUserMessageParam(role='user', content=content))
            elif role == 'assistant':
                converted_messages.append(ChatCompletionAssistantMessageParam(role='assistant', content=content))
            else:
                # Default to user message if role is unknown
                converted_messages.append(ChatCompletionUserMessageParam(role='user', content=content))
        
        return converted_messages
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """Make a chat completion request using the OpenAI SDK.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'.
            temperature: Sampling temperature between 0 and 2.
            max_tokens: Maximum number of tokens to generate.
            
        Returns:
            The completion response as a dictionary.
            
        Raises:
            OpenAIError: If the API returns an error.
            LLMError: For other types of errors.
        """
        try:
            converted_messages = self._convert_messages(messages)
            response: ChatCompletion = self.client.chat.completions.create(
                model=self.basic_model,
                messages=converted_messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Convert the SDK response to our expected format
            message = response.choices[0].message
            if message.content is None:
                raise LLMError("No content in response")
                
            return {
                "role": message.role,
                "content": message.content
            }
            
        except Exception as e:
            self._handle_error(e)
            # This line is unreachable due to NoReturn type on _handle_error,
            # but we need it for type checking
            return {"role": "error", "content": "Error occurred"}
    
    def _convert_to_response_input(self, messages: List[Dict[str, str]]) -> ResponseInputParam:
        """Convert our message format to OpenAI ResponseInputParam format."""
        return tuple({"role": msg["role"], "content": msg["content"]} for msg in messages)

    def structured_completion(
        self,
        messages: List[Dict[str, str]],
        schema: Dict[str, Any],
        name: str = "structure",
        temperature: float = 0.7,
        max_tokens: int = 10000,
        use_detailed_model: bool = False
    ) -> Dict[str, Any]:
        """Make a structured completion request using the OpenAI SDK.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'.
            schema: JSON schema for the response.
            name: name to associate with the structured schema.
            temperature: Sampling temperature between 0 and 2.
            max_tokens: Maximum number of tokens to generate.
            use_detailed_model: Whether to use the detailed model.
            
        Returns:
            The structured completion response as a dictionary.
            
        Raises:
            OpenAIError: If the API returns an error.
            LLMError: For other types of errors.
        """
        try:
            # Convert messages to the format expected by the API
            input_messages = [{"role": msg["role"], "content": msg["content"]} for msg in messages]
            
            response = self.client.responses.create(
                model=self.detailed_model if use_detailed_model else self.basic_model,
                input=cast(Any, input_messages),  # Type cast since we know the structure matches
                temperature=temperature,
                max_output_tokens=max_tokens,
                text={
                    "format": {
                        "type": "json_schema",
                        "name": name,
                        "strict": True,
                        "schema": schema
                    }
                }
            )
            
            result = response.output_text
            try:
                return extract_json(response.output_text)
            except Exception as e:
                print(result)
                raise
            
        except Exception as e:
            self._handle_error(e)
            return {"error": "Error occurred"}