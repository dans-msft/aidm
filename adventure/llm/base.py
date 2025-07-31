"""Base classes for LLM providers."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import json
import asyncio

class LLMError(Exception):
    """Base exception for LLM API errors."""
    def __init__(self, message: str, status_code: Optional[int] = None, response_content: Optional[str] = None):
        self.message = message
        self.status_code = status_code
        self.response_content = response_content
        super().__init__(self._format_error())
    
    def _format_error(self) -> str:
        """Format the error message with all available details."""
        error_parts = [f"LLM API Error: {self.message}"]
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

class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """Get a chat completion from the LLM.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys.
            temperature: Controls randomness (0.0 to 1.0).
            max_tokens: Maximum number of tokens to generate.
            
        Returns:
            Dictionary containing the LLM response.
            
        Raises:
            LLMError: If the API request fails.
        """
        pass
    
    @abstractmethod
    async def structured_completion(
        self,
        messages: List[Dict[str, str]],
        schema: Dict[str, Any],
        name: str = "structure",
        temperature: float = 0.7,
        max_tokens: int = 10000,
        use_detailed_model: bool = False
    ) -> Dict[str, Any]:
        """Get a structured (JSON) completion from the LLM.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys.
            schema: JSON schema defining the expected response structure.
            temperature: Controls randomness (0.0 to 1.0).
            max_tokens: Maximum number of tokens to generate.
            use_detailed_model: True to use a more detailed (expensive) model.
            
        Returns:
            Dictionary containing the structured LLM response.
            
        Raises:
            LLMError: If the API request fails.
        """
        pass 