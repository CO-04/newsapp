from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import CustomUser


class BootstrapFormMixin:
    """
    Mixin that adds Bootstrap's 'form-control' CSS class to every visible
    form widget.  Applied by iterating over fields in __init__ so subclasses
    need no per-field configuration.
    """

    _CHECK_WIDGETS = (
        forms.CheckboxInput,
        forms.CheckboxSelectMultiple,
        forms.RadioSelect,
    )

    def __init__(self, *args, **kwargs):
        """Apply Bootstrap classes to all field widgets on initialisation."""
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            css = widget.attrs.get('class', '')
            if isinstance(widget, self._CHECK_WIDGETS):
                if 'form-check-input' not in css:
                    widget.attrs['class'] = (
                        css + ' form-check-input'
                    ).strip()
            else:
                if 'form-control' not in css:
                    widget.attrs['class'] = (
                        css + ' form-control'
                    ).strip()


class RegistrationForm(BootstrapFormMixin, UserCreationForm):
    """
    Unified registration form for all user roles.

    A 'role' dropdown lets the user self-select Reader, Journalist, or Editor.
    The view reads this choice and sets it on the user instance before saving.

    Improvements over the two-form pattern
    --------------------------------------
    - Single form replaces separate per-role registration forms.
    - email is validated for uniqueness before saving.
    - No unused fields.
    """

    role = forms.ChoiceField(choices=CustomUser.ROLE_CHOICES)

    class Meta:
        """Form configuration: model, field order."""

        model  = CustomUser
        fields = ['username', 'email', 'role', 'password1', 'password2']

    def clean_email(self):
        """Ensure the submitted email address is not already registered."""
        email = self.cleaned_data['email'].lower()
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError(
                'An account with this email address already exists.'
            )
        return email

    def save(self, commit=True):
        """Save the user with the selected role applied."""
        user = super().save(commit=False)
        user.role = self.cleaned_data['role']
        if commit:
            user.save()
        return user
