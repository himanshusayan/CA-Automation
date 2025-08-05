from importlib import import_module

# Dynamically import router modules so “from app.routers import emails” works
_module_names = [
    "companies",
    "emails",
    "reminders",
]

for _name in _module_names:
    import_module(f"{__name__}.{_name}")

# Nothing else is required in this file
