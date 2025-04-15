"""
Dependency Injection

This module provides a simple dependency injection container.
"""

from typing import Any, Dict, Optional, Type, TypeVar, cast

T = TypeVar('T')


class DependencyContainer:
    """Simple dependency injection container."""
    
    def __init__(self):
        """Initialize the container."""
        self._instances: Dict[str, Any] = {}
        self._factories: Dict[str, callable] = {}
    
    def register_instance(self, interface_class: Any, instance: Any, name: Optional[str] = None) -> None:
        """
        Register an existing instance for an interface.
        
        Args:
            interface_class: Interface class or string key
            instance: Instance to register
            name: Optional name for the registration
        """
        key = self._get_key(interface_class, name)
        self._instances[key] = instance
    
    def register_factory(self, interface_class: Type[T], factory: callable, name: Optional[str] = None) -> None:
        """
        Register a factory function for an interface.
        
        Args:
            interface_class: Interface class
            factory: Factory function that creates an instance
            name: Optional name for the registration
        """
        key = self._get_key(interface_class, name)
        self._factories[key] = factory
    
    def register_class(self, interface_class: Type[T], concrete_class: Type[T], name: Optional[str] = None) -> None:
        """
        Register a concrete class for an interface.
        
        Args:
            interface_class: Interface class
            concrete_class: Concrete class to instantiate
            name: Optional name for the registration
        """
        self.register_factory(interface_class, lambda c: concrete_class(), name)
    
    def resolve(self, interface_class: Any, name: Optional[str] = None) -> Any:
        """
        Resolve an interface to an instance.
        
        Args:
            interface_class: Interface class or string key
            name: Optional name for the registration
            
        Returns:
            Instance of the interface
            
        Raises:
            KeyError: If the interface is not registered
        """
        key = self._get_key(interface_class, name)
        
        # Return existing instance if available
        if key in self._instances:
            return self._instances[key]
        
        # Create instance using factory if available
        if key in self._factories:
            instance = self._factories[key](self)
            self._instances[key] = instance
            return instance
        
        raise KeyError(f"No registration found for {key}")
    
    def _get_key(self, interface_class: Any, name: Optional[str] = None) -> str:
        """
        Get the key for a registration.
        
        Args:
            interface_class: Interface class or string key
            name: Optional name
            
        Returns:
            Registration key
        """
        if isinstance(interface_class, str):
            base_key = interface_class
        else:
            base_key = interface_class.__name__
            
        return f"{base_key}:{name}" if name else base_key


# Create a global container instance
container = DependencyContainer()
