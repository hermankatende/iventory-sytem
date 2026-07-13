import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class StrongPasswordPolicyValidator:
    def validate(self, password: str, user=None) -> None:
        checks = [
            (r"[A-Z]", _("Password must contain at least one uppercase letter.")),
            (r"[a-z]", _("Password must contain at least one lowercase letter.")),
            (r"[0-9]", _("Password must contain at least one number.")),
            (r"[^A-Za-z0-9]", _("Password must contain at least one special character.")),
        ]

        errors = [message for pattern, message in checks if not re.search(pattern, password)]
        if errors:
            raise ValidationError(errors)

    def get_help_text(self) -> str:
        return _("Your password must contain uppercase, lowercase, numeric, and special characters.")
