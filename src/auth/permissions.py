from src.auth.permission_enum import Actions, Modules, Service

permissions = [
    {
        "service": Service.Marketer.name,
        "serviceTitle": Service.Marketer.value,
        "module": Modules.All.name,
        "moduleTitle": Modules.All.value,
        "action": None,
        "actionTitle": None,
    }
]
