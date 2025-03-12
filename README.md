# py-meta

A collection of types and utility functions to enhance the Python development experience with meta-programming and advanced module management.

## Features

### `import_submodules`

Dynamically imports all submodules of a package, with optional recursive importing and exclusion patterns.

```python
from py_meta import import_submodules

# Import all submodules in the current package (no need to pass __name__)
modules = import_submodules()

# Import all submodules in a specific package
modules = import_submodules('my_library.utils')

# Import non-recursively with exclusions
modules = import_submodules(recursive=False, exclude=['config', 'legacy'])
```

### `register_entry_point`

Creates a convenient entry point for CLI scripts and modules. Can be used as a decorator.

```python
from py_meta import register_entry_point

@register_entry_point
def process_data(files=None):
    files = files or ["default.txt"]
    for file in files:
        print(f"Processing {file}")
    return 0
    
# When this script is run directly, process_data will be called
# When imported, process_data is still a normal function
```

### `EntryPoint`

A class to wrap entry point functions with default arguments.

```python
from py_meta import EntryPoint
import logging

logger = logging.getLogger('my_app')

def my_function(path, verbose=False):
    # Process files at path
    return 0

entry = EntryPoint(
    func=my_function,
    init_kwargs={'verbose': True},
    logger=logger
)

# Run with custom arguments
result = entry.run('/path/to/data')
```

## Enterprise Features

- **Type Hinting**: Full type annotations for better IDE support
- **Exception Handling**: Robust error catching and reporting
- **Flexible Logging**: Configurable logging throughout
- **Keyboard Interrupts**: Proper handling of Ctrl+C with appropriate exit codes
- **Decorator API**: Functions can be decorated for ease of use
- **Automatic Module Detection**: No need to explicitly pass `__name__` parameter

## Installation

```
# Coming soon
```

## License

See the LICENSE file for details.
