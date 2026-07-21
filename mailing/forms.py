from django import forms
from .models import Mailing
from django.utils import timezone


class MailingForm(forms.ModelForm):
    """Форма для создания и редактирования рассылки."""

    message = forms.ModelChoiceField(
        queryset=None,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Сообщение',
        required=True
    )

    class Meta:
        model = Mailing

        fields = ['start_time', 'end_time', 'recipients']

        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'recipients': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if 'message' in self.fields:
            self.fields['message'].queryset = self._meta.model.message.field.related_model.objects.all()

        for time_field in ['start_time', 'end_time']:
            if time_field in self.fields:
                self.fields[time_field].input_formats = ['%Y-%m-%dT%H:%M']

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if start_time and start_time < timezone.now():
            self.add_error('start_time', 'Дата начала не может быть в прошлом.')

        if start_time and end_time and start_time >= end_time:
            self.add_error('end_time', 'Дата окончания должна быть позже даты начала.')
