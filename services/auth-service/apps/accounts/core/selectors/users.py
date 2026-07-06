from apps.accounts.core.models import User


def get_active_user_by_id(user_id):
    return User.objects.filter(id=user_id, is_active=True).first()
