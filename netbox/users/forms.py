from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm as DjangoPasswordChangeForm
from django.utils.html import mark_safe

from netbox.preferences import PREFERENCES
from utilities.forms import BootstrapMixin, DateTimePicker, StaticSelect
from utilities.utils import flatten_dict
from .models import Token, UserConfig


class LoginForm(BootstrapMixin, AuthenticationForm):
    pass


class PasswordChangeForm(BootstrapMixin, DjangoPasswordChangeForm):
    pass


class UserConfigFormMetaclass(forms.models.ModelFormMetaclass):

    def __new__(mcs, name, bases, attrs):

        # Emulate a declared field for each supported user preference
        preference_fields = {}
        for field_name, preference in PREFERENCES.items():
            description = f'{preference.description}<br />' if preference.description else ''
            help_text = f'{description}<code>{field_name}</code>'
            field_kwargs = {
                'label': preference.label,
                'choices': preference.choices,
                'help_text': mark_safe(help_text),
                'coerce': preference.coerce,
                'required': False,
                'widget': StaticSelect,
            }
            preference_fields[field_name] = forms.TypedChoiceField(**field_kwargs)
        attrs.update(preference_fields)

        return super().__new__(mcs, name, bases, attrs)


class UserConfigForm(BootstrapMixin, forms.ModelForm, metaclass=UserConfigFormMetaclass):

    class Meta:
        model = UserConfig
        fields = ()

    def __init__(self, *args, instance=None, **kwargs):

        # Get initial data from UserConfig instance
        initial_data = flatten_dict(instance.data)
        kwargs['initial'] = initial_data

        super().__init__(*args, instance=instance, **kwargs)

    def save(self, *args, **kwargs):

        # Set UserConfig data
        for pref_name, value in self.cleaned_data.items():
            self.instance.set(pref_name, value, commit=False)

        return super().save(*args, **kwargs)


class TokenForm(BootstrapMixin, forms.ModelForm):
    key = forms.CharField(
        required=False,
        help_text="If no key is provided, one will be generated automatically."
    )

    class Meta:
        model = Token
        fields = [
            'key', 'write_enabled', 'expires', 'description',
        ]
        widgets = {
            'expires': DateTimePicker(),
        }
