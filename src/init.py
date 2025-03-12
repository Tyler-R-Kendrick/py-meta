import pkgutil
import importlib
import inspect
from typing import Dict, Set, Optional, Union, List, Any, Mapping

class PackageMetadata:
    """
    A class to hold package metadata.
    """
    def __init__(
        self,
        name: str,
        description: str,
        version: Optional[str] = '0.1.0',
    ):
        self.name = name
        self.description = description
        self.version = version

class PackageOptions:
    """
    A class to hold package options.
    """
    def __init__(
        self,
        metadata: PackageMetadata,
        exclude_modules: Optional[Union[Set[str], List[str]]] = None,
        alias_map: Optional[Dict[str, str]] = None
    ):
        self.metadata = metadata
        self.exclude_modules = exclude_modules or set()
        self.alias_map = alias_map or {}

def init_package(
    package_options: PackageOptions,
    exclude_modules: Optional[Union[Set[str], List[str]]] = None,
    globals_dict: Optional[Dict[str, Any]] = None,
):
    """
    Initialize a module with metadata.
    
    Args:
        package_options: Options for the package.
        exclude_modules: Names to exclude from importing.
        globals_dict: Dictionary of global variables to use.
    """
    import_submodules(
        package_name=package_options.metadata.name,
        exclude=exclude_modules,
        alias_map=package_options.alias_map,
        globals_dict=globals_dict)

def import_submodules(
    package_name: Optional[str] = None,
    *,
    recursive: bool = True,
    exclude: Optional[Union[Set[str], List[str]]] = None,
    alias_map: Optional[Mapping[str, str]] = None,
    globals_dict: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Dynamically imports all submodules of the package.
    
    Args:
        package_name: The package name (e.g., 'mypackage'). If None, uses the 
                      caller's module name from globals_dict.
        recursive: Whether to recursively import subpackages.
        exclude: Names to exclude from importing.
        alias_map: Mapping from module names to aliases to use when importing.
        globals_dict: Dictionary of global variables to use (defaults to caller's globals).
        
    Returns:
        Dict mapping from module names (or their aliases) to imported module objects.
    
    Examples:
        # Import all submodules in the current package
        modules = import_submodules(globals_dict=globals())
        
        # Import all submodules in a specific package
        modules = import_submodules('my_library.utils')
        
        # Import non-recursively with exclusions
        modules = import_submodules(recursive=False, exclude=['config', 'legacy'])
        
        # Import with aliases
        modules = import_submodules(alias_map={'database': 'db', 'utilities': 'utils'})
    """
    # Handle optional package_name parameter
    if package_name is None:
        if globals_dict is None:
            globals_dict = inspect.currentframe().f_back.f_globals
        package_name = globals_dict.get('__name__', '')
    
    # Convert exclude to a set for O(1) lookups
    exclude_set = set(exclude or [])
    
    # Initialize alias map if not provided
    alias_map = alias_map or {}
    
    # Import the package
    try:
        package = importlib.import_module(package_name)
    except ImportError:
        # Return empty dict if the package doesn't exist or can't be imported
        return {}
    
    imported_modules = {}
    
    # Check if the package has a proper __path__ attribute
    if not hasattr(package, '__path__'):
        return imported_modules
    
    # Iterate through package contents
    for _, module_name, is_pkg in pkgutil.walk_packages(
        package.__path__, 
        prefix=f"{package.__name__}."
    ):
        # Extract the short name from the fully qualified name
        short_name = module_name.split('.')[-1]
        
        # Skip modules that should be excluded
        if short_name.startswith('_') or short_name in exclude_set:
            continue
        
        # Import the module
        try:
            module = importlib.import_module(module_name)
            
            # Check if module should use an alias
            module_key = module_name
            if short_name in alias_map:
                # Use the alias for the module key
                module_key = module_name.rsplit('.', 1)[0] + '.' + alias_map[short_name]
            
            imported_modules[module_key] = module
            
            # Update the package's __all__ attribute if it exists
            _alias = alias_map.get(short_name, short_name)
            package.__all__ = getattr(package, '__all__', [])
            if _alias not in package.__all__:
                package.__all__.append(_alias)
                
            # Recursively import submodules if requested
            if recursive and is_pkg:
                sub_modules = import_submodules(
                    module_name,
                    recursive=recursive,
                    exclude=exclude_set,
                    alias_map=alias_map
                )
                imported_modules.update(sub_modules)
                
        except ImportError as e:
            # Silently skip modules that can't be imported
            # In an enterprise setting, you might want to log this instead
            pass
            
    return imported_modules
