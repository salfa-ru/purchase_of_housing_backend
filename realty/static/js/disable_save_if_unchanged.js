// Выключаем кнопки сохранения записей пока не было внесено никаких исправлений.
// Изначально используется только в админке Realty (для удобства Модераторов).

document.addEventListener("DOMContentLoaded", function() {
    const form = document.getElementById("realty_form");

    const saveButton = document.querySelector("[name='_save']");
    const continueButton = document.querySelector("[name='_continue']");
    const addAnotherButton = document.querySelector("[name='_addanother']");

    // Отключаем все три кнопки
    function disableButtons() {
        if (saveButton) saveButton.disabled = true;
        if (continueButton) continueButton.disabled = true;
        if (addAnotherButton) addAnotherButton.disabled = true;
    }

    // Включаем все три кнопки
    function enableButtons() {
        if (saveButton) saveButton.disabled = false;
        if (continueButton) continueButton.disabled = false;
        if (addAnotherButton) addAnotherButton.disabled = false;
    }

    // Сначала все кнопки отключаются
    disableButtons();

    // Включаются, если пользователь хоть что-то исправил в форме
    form.addEventListener("input", function(event) {
        if (event.target.matches("input, select, textarea")) {
            enableButtons();
        }
    });
});
