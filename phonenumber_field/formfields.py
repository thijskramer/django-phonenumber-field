import phonenumbers
from django.conf import settings
from django.core import validators
from django.core.exceptions import ValidationError
from django.forms.fields import CharField
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _

from phonenumber_field.phonenumber import to_python, validate_region
from phonenumber_field.validators import validate_international_phonenumber
from phonenumber_field.widgets import PhoneNumberInternationalFallbackWidget


class PhoneNumberField(CharField):
    default_validators = [validate_international_phonenumber]
    widget = PhoneNumberInternationalFallbackWidget

    def __init__(self, *args, region=None, widget=None, **kwargs):
        validate_region(region)
        self.region = region or getattr(settings, "PHONENUMBER_DEFAULT_REGION", None)

        if widget is None:
            try:
                widget = self.widget(region=self.region)
            except TypeError:
                widget = self.widget()

        super().__init__(*args, widget=widget, **kwargs)
        self.widget.input_type = "tel"

        if "invalid" not in self.error_messages:
            if self.region:
                number = phonenumbers.example_number(self.region)
                example_number = to_python(number).as_national
                # Translators: {example_number} is a national phone number.
                error_message = _(
                    "Enter a valid phone number (e.g. {example_number}) "
                    "or a number with an international call prefix."
                )
            else:
                example_number = "+12125552368"  # Ghostbusters
                # Translators: {example_number} is an international phone number.
                error_message = _("Enter a valid phone number (e.g. {example_number}).")
            self.error_messages["invalid"] = format_lazy(
                error_message, example_number=example_number
            )

    def to_python(self, value):
        phone_number = to_python(value, region=self.region)

        if phone_number in validators.EMPTY_VALUES:
            return self.empty_value

        if phone_number and not phone_number.is_valid():
            raise ValidationError(self.error_messages["invalid"])

        return phone_number
