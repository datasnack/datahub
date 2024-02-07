import pkgutil
import importlib

# Get the current module
current_module = __name__

# Iterate over all modules in the current package
for _, module_name, _ in pkgutil.iter_modules([current_module]):
   # Import the module
   module = importlib.import_module(f'.{module_name}', current_module)
   
   # Add the module's attributes to the current namespace
   globals().update({name: value for name, value in module.__dict__.items()})