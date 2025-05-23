from django import template
from django.db.models import QuerySet

register = template.Library()


@register.filter
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def divide(value, arg):
    try:
        return int(float(value) / float(arg))
    except (ValueError, TypeError, ZeroDivisionError):
        return 0


@register.filter
def filter_by(queryset, expr):
    """
    クエリセットをフィルタリングするテンプレートフィルター
    使用例: {{ executions|filter_by:"result='PASS'" }}
    """
    if not isinstance(queryset, QuerySet):
        return []

    try:
        key, value = expr.split("=")
        value = value.strip("'\"")
        return queryset.filter(**{key: value})
    except (ValueError, TypeError):
        return []


@register.simple_tag
def define(val=None):
    return val
