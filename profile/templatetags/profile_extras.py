from django import template


register = template.Library()


@register.filter
def model_name(obj):
    try:
        return obj.__class__.__name__
    except AttributeError:
        return None


@register.filter
def get_verbose_name(obj):
    return obj._meta.verbose_name


@register.filter
def get_verbose_name_plural(obj):
    return obj._meta.verbose_name_plural
