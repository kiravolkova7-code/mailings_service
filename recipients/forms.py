from django import forms
from .models import Recipients, Message


class RecipientForm(forms.ModelForm):
    class Meta:
        model = Recipients
        fields = ["first_name", "last_name", "surname", "email", "comment"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "surname": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.TextInput(attrs={"class": "form-control"}),
            "comment": forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
        }


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ["subject", "body_message"]
        widgets = {
            "subject": forms.TextInput(attrs={"class": "form-control"}),
            "body_message": forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
        }
