
from django import forms
from .models import Mailing


class MailingForm(forms.ModelForm):
    """Форма для создания и редактирования рассылки."""

    class Meta:
        model = Mailing

        fields = ['start_time', 'end_time', 'message', 'recipients']

        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),

            'recipients': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for time_field in ['start_time', 'end_time']:
            if time_field in self.fields:
                self.fields[time_field].input_formats = ['%Y-%m-%dT%H:%M']

    def clean(self):
        """
        Повторяем логику валидации из модели на уровне формы,
        чтобы ошибки выводились прямо над полями в браузере.
        """
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        from django.utils import timezone

        if start_time and start_time < timezone.now():
            self.add_error('start_time', 'Дата начала не может быть в прошлом.')

        if start_time and end_time and start_time >= end_time:
            self.add_error('end_time', 'Дата окончания должна быть позже даты начала.')