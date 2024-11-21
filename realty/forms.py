from django import forms
from django.core.exceptions import ValidationError
from realty.models import Realty
from realty_values.models import RealtyAdvStatus


class RealtyForm(forms.ModelForm):

    def __init__(self, *args, request=None, **kwargs):
        # Реквест из админки - приходит, чтобы узнать пользователя –
        # чтобы можно было запрещать модератору лишние действия со Статусом
        self.request = request
        super().__init__(*args, **kwargs)

        # Не даем возможности выбрать пустой Статус (никому)
        self.fields['realty_status'].empty_label = None
        self.fields['realty_status'].required = True

        # Показываем только возможные варианты Статусов
        self.set_status_choices()

        # Меняем подсказки, какие Статусы возможны
        self.set_restricted_status_help_text()

    def set_status_choices(self):
        """ Показываем только возможные варианты Статусов в админке  """

        # В случае, если создается НОВАЯ ЗАПИСЬ, выдаем Админу возможность выбрать любой статус
        if not self.instance or not self.instance.id:
            return

        current_status = self.instance.realty_status

        if not self.request.user.is_superuser:
            # Механизм отображения только возможных переходов
            if current_status.status == 'На модерации':
                allowed_statuses = RealtyAdvStatus.objects.filter(status__in=['Активно', 'Отклонено'])
            elif current_status.status == 'Активно':
                allowed_statuses = RealtyAdvStatus.objects.filter(status='Отклонено')
            elif current_status.status == 'В архиве':
                allowed_statuses = RealtyAdvStatus.objects.filter(status='В архиве')
            else:  # 'Отклонено' не может быть изменен на другой Статус.
                allowed_statuses = RealtyAdvStatus.objects.filter(status='Отклонено')

            # Отправляем это все в админку
            self.fields['realty_status'].queryset = RealtyAdvStatus.objects.filter(
                id__in=[current_status.id] + list(allowed_statuses.values_list('id', flat=True)))

    def set_restricted_status_help_text(self):
        """ Отображение справки о возможных переходах статуса"""

        if not self.instance or not self.instance.id:
            return  # Не показываем, если создается новая запись

        current_status = self.instance.realty_status.status

        if current_status == 'На модерации':
            self.fields['realty_status'].help_text = ("Вы можете изменить статус только на "
                                                      "<strong>'Активно'</strong> "
                                                      "или <strong>'Отклонено'</strong>.")
        elif current_status == 'Активно':
            self.fields['realty_status'].help_text = "Вы можете изменить статус только на <strong>'Отклонено'</strong>."
        elif current_status == 'Отклонено':
            self.fields['realty_status'].help_text = ("<span style='color: red;'>"
                                                      "Статус уже <strong>'Отклонено'</strong> и не может быть изменен </span>")
        elif current_status == 'В архиве':
            self.fields['realty_status'].help_text = ("<span style='color: darkorange;'>"
                                                      "Не предусмотрено изменения статуса <strong>'В архиве'</strong> через админку </span>")

        if self.request.user.is_superuser:
            self.fields['realty_status'].help_text = ("При данном статусе модератор увидит следующее сообщение: <br>"
                                                      + self.fields['realty_status'].help_text)

    class Meta:
        model = Realty
        # fields = ('realty_status',) # Остаток кода, где в админке можно было редактировать только Статус
        fields = '__all__'  # Теперь показываются все поля, а редактируемость определяется в админке

    def clean(self):
        cleaned_data = super().clean()

        # Админ может менять Статус как захочет, без проверки
        if self.request and self.request.user.is_superuser:
            return cleaned_data

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
