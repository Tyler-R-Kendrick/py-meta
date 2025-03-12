import sys
import asyncio
import inspect
import logging
from typing import Any, Callable, Tuple, Dict, Optional, TypeVar, cast, Union, List

# Create a default logger but don't make it the only option
default_logger = logging.getLogger(__name__)
default_logger.setLevel(logging.INFO)

class EntryPoint:
    """
    A helper class to wrap an entry point function with default arguments.
    """
    def __init__(
        self, 
        func: Callable[..., Any],
        init_args: Tuple[Any, ...] = (), 
        init_kwargs: Optional[Dict[str, Any]] = None,
        *, 
        logger: Optional[logging.Logger] = None
    ) -> None:
        """
        Initialize an entry point.
        
        Args:
            func: The target function to be invoked.
            init_args: Default positional arguments for func.
            init_kwargs: Default keyword arguments for func.
            logger: The logger instance to use for logging.
        """
        self.func = func
        self.init_args = init_args
        self.init_kwargs = init_kwargs or {}
        self.logger = logger or default_logger

    def run(self, *args: Any, **kwargs: Any) -> Any:
        """
        Run the entry point function with the provided arguments.
        
        If no runtime arguments are provided, will use sys.argv[1:] as the first argument.
        
        Args:
            *args: Positional arguments to pass to the function.
            **kwargs: Keyword arguments to pass to the function.
            
        Returns:
            The return value of the function.
        """
        # If no runtime arguments are provided, default to sys.argv[1:].
        args_to_use = args or (sys.argv[1:],)
        combined_args = self.init_args + args_to_use
        combined_kwargs = {**self.init_kwargs, **kwargs}
        
        try:
            if asyncio.iscoroutinefunction(self.func):
                return asyncio.run(self.func(*combined_args, **combined_kwargs))
            else:
                return self.func(*combined_args, **combined_kwargs)
        except Exception as e:
            self.logger.exception(f"Error running entry point {self.func.__name__}: {e}")
            raise


def register_entry_point(
    func: Callable[..., Any],
    *,
    entry_name: str = "main",
    init_args: Optional[Tuple[Any, ...]] = None,
    init_kwargs: Optional[Dict[str, Any]] = None,
    target_globals: Optional[Dict[str, Any]] = None,
    logger: Optional[logging.Logger] = None,
    exit_on_completion: bool = True
) -> Callable[..., Any]:
    """
    Registers a callable under the name `entry_name` into the given globals.
    
    If target_globals is not provided, it defaults to using the caller's globals.
    
    Args:
        func: The target function to be invoked.
        entry_name: The name under which to register the callable (default "main").
        init_args: Default positional arguments for func.
        init_kwargs: Default keyword arguments for func.
        target_globals: The globals() dict of the calling module.
        logger: The logger instance to use for logging messages.
        exit_on_completion: Whether to call sys.exit() with the return value 
                            if the function returns an int.
    
    Raises:
        RuntimeError: If a callable named `entry_name` already exists.
    
    Examples:
        >>> @register_entry_point
        ... def process_data(files=None):
        ...     files = files or ["default.txt"]
        ...     for file in files:
        ...         print(f"Processing {file}")
        ...     return 0
        
        >>> @register_entry_point(target_globals=globals())
        ... def another_function():
        ...     pass
    """
    init_args = init_args or ()
    init_kwargs = init_kwargs or {}
    logger_to_use = logger or default_logger
    
    # Use explicit globals if provided; otherwise get from caller frame
    if target_globals is None:
        target_globals = inspect.currentframe().f_back.f_globals
        
    # Check if entry_name already exists in the target globals
    if entry_name in target_globals:
        existing = target_globals[entry_name]
        logger_to_use.error("Entry point %r already defined: %r", entry_name, existing)
        raise RuntimeError(
            f"A callable named {entry_name!r} is already defined in module "
            f"{target_globals.get('__name__', '<unknown>')}: {existing!r}"
        )
        
    ep = EntryPoint(
        func=func, 
        init_args=init_args, 
        init_kwargs=init_kwargs, 
        logger=logger_to_use
    )
    
    def _entry(*args: Any, **kwargs: Any) -> Any:
        """Entry point wrapper that handles sys.exit() if needed."""
        try:
            result = ep.run(*args, **kwargs)
            if exit_on_completion and isinstance(result, int):
                sys.exit(result)
            return result
        except KeyboardInterrupt:
            logger_to_use.info("Operation interrupted by user")
            sys.exit(130)  # Standard exit code for SIGINT
    
    # Copy the function metadata to the entry point
    _entry.__name__ = func.__name__
    _entry.__doc__ = func.__doc__
    _entry.__module__ = func.__module__
    
    target_globals[entry_name] = _entry
    logger_to_use.info(
        "Registered entry point %r in module %r", 
        entry_name, 
        target_globals.get("__name__", "<unknown>")
    )
    
    # If this module is being executed directly, run the injected entry point.
    if target_globals.get("__name__") == "__main__":
        _entry()
        
    return func  # Return the original function for use as a decorator
