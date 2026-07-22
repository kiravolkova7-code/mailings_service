from django.contrib import admin
from recipients.models import Message, Recipients

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('subject',)
    search_fields = ('subject', 'body_message')


@admin.register(Recipients)
class RecipientsAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'email')
    search_fields = ('email', 'first_name', 'last_name')
    readonly_fields = ('full_name',)

    @admin.display(description='Полное имя')
    def full_name(self, obj):
        parts = [obj.first_name]
        if obj.surname:
            parts.append(obj.surname)
        if obj.last_name:
            parts.append(obj.last_name)
        return ' '.join(parts)
