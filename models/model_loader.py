"""
Model loader factory for different AI models.
"""
from typing import Dict, Any, Optional
import logging
from .base_model import BaseModel
from .claude_api_wrapper import ClaudeModel
from .openai_api_wrapper import OpenAIModel

logger = logging.getLogger(__name__)


class ModelLoader:
    """Factory class for loading different AI models."""
    
    SUPPORTED_MODELS = {
        "claude": ClaudeModel,
        "claude-3-sonnet-20240229": ClaudeModel,
        "claude-3-opus-20240229": ClaudeModel,
        "claude-3-haiku-20240307": ClaudeModel,
        "gpt-4": OpenAIModel,
        "gpt-4-turbo": OpenAIModel,
        "gpt-3.5-turbo": OpenAIModel,
        "openai": OpenAIModel,
    }
    
    @classmethod
    def get_supported_models(cls) -> list:
        """Return list of supported model names."""
        return list(cls.SUPPORTED_MODELS.keys())
    
    @classmethod
    def load_model(cls, model_name: str, api_key: Optional[str] = None, **kwargs) -> BaseModel:
        """
        Load a model by name.
        
        Args:
            model_name: Name of the model to load
            api_key: API key for the model (optional, will use environment variable)
            **kwargs: Additional arguments to pass to the model constructor
            
        Returns:
            BaseModel: Initialized model instance
            
        Raises:
            ValueError: If model name is not supported
        """
        # Normalize model name
        model_name_lower = model_name.lower()
        
        # Handle generic model names
        if model_name_lower in ["claude", "anthropic"]:
            model_class = ClaudeModel
            actual_model_name = kwargs.get("actual_model_name", "claude-3-sonnet-20240229")
        elif model_name_lower in ["openai", "gpt"]:
            model_class = OpenAIModel
            actual_model_name = kwargs.get("actual_model_name", "gpt-4")
        elif model_name in cls.SUPPORTED_MODELS:
            model_class = cls.SUPPORTED_MODELS[model_name]
            actual_model_name = model_name
        else:
            raise ValueError(f"Unsupported model: {model_name}. Supported models: {cls.get_supported_models()}")
        
        try:
            logger.info(f"Loading model: {model_name}")
            model = model_class(model_name=actual_model_name, api_key=api_key, **kwargs)
            logger.info(f"Successfully loaded model: {model_name}")
            return model
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {str(e)}")
            raise


def load_model(model_name: str, api_key: Optional[str] = None, **kwargs) -> BaseModel:
    """Convenience function to load a model."""
    return ModelLoader.load_model(model_name, api_key, **kwargs)