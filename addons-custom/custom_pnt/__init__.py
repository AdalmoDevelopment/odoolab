PROJECTS = {
    "logistics": 1,
}
TASK_STAGES = {
    "planned": 2,
    "commercial": 13,
    "manager": 12,
    "closed": 14,
    "discount": 15,
    "invoiced": 16,
    "process": 3,
    "pendingassig": 1,
    "cancelled": 8,
    "done": 7,
}
ACTIVITY_TEAMS = {
    "accounting": 1,
}
GROUPS = {
    "agreement_manager_commercial": 131,
}
DEFAULT_DELIVERY_PARTNER_ID = 6275
DEFAULT_NEW_DU_WIZ_SCALE_PICKUP_ID = 37735
DEFAULT_NEW_DU_WIZ_SCALE_ID = 43

from . import models
from . import wizards
