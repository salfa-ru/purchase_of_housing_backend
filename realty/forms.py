from django import forms
from django.core.exceptions import ValidationError
from realty.models import Realty


class RealtyForm(forms.ModelForm):
    class Meta:
        model = Realty
        fields = ('realty_status',)

    def clean(self):
        cleaned_data = super().clean()

        if self.instance:
            old_instance = Realty.objects.get(id=self.instance.id)
            realty_status = cleaned_data.get('realty_status')
            if old_instance.realty_status.status == 'На модерации':
                if realty_status.status not in ['Активно', 'Отклонено']:
                    raise forms.ValidationError("Статус можно изменить только на 'Активно' или 'Отклонено'.")
            elif old_instance.realty_status.status == 'Активно':
                if realty_status.status != 'Отклонено':
                    raise ValidationError("Статус можно изменить только на 'Отклонено', если он 'Активно'.")
            elif old_instance.realty_status.status == 'Отклонено':
                raise ValidationError("Статус уже 'Отклонено' и не может быть изменен.")

        return cleaned_data
