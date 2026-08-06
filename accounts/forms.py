from django.contrib.auth.forms import SetPasswordForm as DjangoSetPasswordForm
from django.utils.safestring import mark_safe


class SetPasswordForm(DjangoSetPasswordForm):
    """SetPasswordForm with French labels/help text (USE_I18N is off, see
    dgh_intranet/settings/base.py)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["new_password1"].label = "Nouveau mot de passe"
        self.fields["new_password1"].help_text = mark_safe(
            "<ul>"
            "<li>Votre mot de passe ne peut pas trop ressembler à vos autres "
            "informations personnelles.</li>"
            "<li>Votre mot de passe doit contenir au moins 8 caractères.</li>"
            "<li>Votre mot de passe ne peut pas être un mot de passe couramment "
            "utilisé.</li>"
            "<li>Votre mot de passe ne peut pas être entièrement numérique.</li>"
            "</ul>"
        )
        self.fields["new_password2"].label = "Confirmation du nouveau mot de passe"
        self.fields["new_password2"].help_text = (
            "Saisissez à nouveau le même mot de passe, pour vérification."
        )
