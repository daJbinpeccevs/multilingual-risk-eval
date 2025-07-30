"""
Base model interface for multilingual risk evaluation.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class BaseModel(ABC):
    """Abstract base class for all language models."""
    
    def __init__(self, model_name: str, api_key: Optional[str] = None):
        self.model_name = model_name
        self.api_key = api_key
        
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate response for a given prompt."""
        pass
    
    @abstractmethod
    def batch_generate(self, prompts: List[str], **kwargs) -> List[str]:
        """Generate responses for multiple prompts."""
        pass
    
    def validate_response(self, response: str) -> bool:
        """Validate that the response is not empty or invalid."""
        return response is not None and len(response.strip()) > 0
    
    def get_model_info(self) -> Dict[str, Any]:
        """Return model information."""
        return {
            "model_name": self.model_name,
            "type": self.__class__.__name__
        }