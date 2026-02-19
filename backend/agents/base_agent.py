"""
Base Agent Class
All agents inherit from this
"""
import asyncio
from abc import ABC, abstractmethod

class BaseAgent(ABC):
    def __init__(self, name: str):
        self.name = name
        print(f"[Agent: {self.name}] Initialized")
    
    @abstractmethod
    async def process(self, data: dict) -> dict:
        """
        Process data - must be implemented by child classes
        
        Args:
            data: Input data dictionary
            
        Returns:
            Result dictionary
        """
        pass
    
    def log(self, message: str):
        """Log a message"""
        print(f"[Agent: {self.name}] {message}")