from .models import Category


def nav_categories(request):
    return {'nav_categories': Category.objects.filter(is_active=True)}
