from django import template

register = template.Library()


@register.filter(name="add_class")
def add_class(field, css_class):
    """Render a bound field's widget with an extra CSS class appended.

    Template-only stand-in for setting widget attrs in forms.py (out of
    scope for this restyle): re-renders the field through Django's own
    as_widget(), preserving whatever attrs the widget already carries
    (type, autocomplete, maxlength, required, ...) and only adding to
    `class`.
    """
    attrs = dict(field.field.widget.attrs)
    existing = attrs.get("class", "")
    attrs["class"] = f"{existing} {css_class}".strip()
    return field.as_widget(attrs=attrs)
