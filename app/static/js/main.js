// Общие JavaScript функции для системы управления рисками ИБ

// Функция для подтверждения удаления
function confirmDelete(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// Функция для показа уведомлений
function showNotification(message, type = 'info') {
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    const container = document.querySelector('.container');
    container.insertAdjacentHTML('afterbegin', alertHtml);
}

// Функция для загрузки данных с сервера
async function fetchData(url) {
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Ошибка при загрузке данных:', error);
        showNotification('Ошибка при загрузке данных', 'danger');
        return null;
    }
}

// Функция для отправки данных на сервер
async function postData(url, data) {
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Ошибка при отправке данных:', error);
        showNotification('Ошибка при отправке данных', 'danger');
        return null;
    }
}

// Функция для обновления данных на странице
function updatePageData(data) {
    // Заглушка для обновления данных на странице
    // Реализация будет зависеть от конкретной страницы
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    // Добавляем обработчики для форм
    const forms = document.querySelectorAll('form[data-ajax]');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(form);
            const data = Object.fromEntries(formData.entries());
            
            postData(form.action, data)
                .then(response => {
                    if (response) {
                        showNotification('Данные успешно сохранены', 'success');
                        // Обновляем страницу или часть страницы
                        location.reload();
                    }
                });
        });
    });
    
    // Добавляем обработчики для кнопок удаления
    const deleteButtons = document.querySelectorAll('[data-delete-url]');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function() {
            const url = this.getAttribute('data-delete-url');
            confirmDelete('Вы уверены, что хотите удалить этот элемент?', () => {
                fetch(url, { method: 'DELETE' })
                    .then(response => {
                        if (response.ok) {
                            showNotification('Элемент успешно удален', 'success');
                            location.reload();
                        } else {
                            showNotification('Ошибка при удалении элемента', 'danger');
                        }
                    });
            });
        });
    });
});