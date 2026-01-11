document.addEventListener('DOMContentLoaded', function() {
    // Загрузка контекстов
    fetch('/api/contexts')
        .then(response => response.json())
        .then(data => {
            const contextSelect = document.getElementById('context_id');
            const assetFormData = document.getElementById('asset-form-data');
            const selectedContextId = assetFormData.dataset.contextId;

            data.forEach(context => {
                const option = document.createElement('option');
                option.value = context.id;
                option.textContent = context.name;
                if (selectedContextId !== null && selectedContextId == context.id) {
                    option.selected = true;
                }
                contextSelect.appendChild(option);
            });
        });

    // Обработчик отправки формы
    document.getElementById('asset-form').addEventListener('submit', function(e) {
        e.preventDefault();

        // Собираем свойства ИБ
        const properties = {
            confidentiality: document.getElementById('confidentiality').value === '+',
            integrity: document.getElementById('integrity').value === '+',
            availability: document.getElementById('availability').value === '+'
        };

        const formData = {
            context_id: parseInt(document.getElementById('context_id').value),
            name: document.getElementById('name').value,
            description: document.getElementById('description').value,
            type: document.getElementById('type').value,
            properties: JSON.stringify(properties),
            evaluation_criteria: document.getElementById('evaluation_criteria') ? document.getElementById('evaluation_criteria').value : '{}',
            impact_score: 0, // будет вычислено автоматически
            impact_matrix: document.getElementById('impact_matrix') ? document.getElementById('impact_matrix').value : '{}',
            cost_value: document.getElementById('cost_value') && document.getElementById('cost_value').value ? document.getElementById('cost_value').value : undefined,
            value_without_dependencies: document.getElementById('value_without_dependencies') && document.getElementById('value_without_dependencies').value ? document.getElementById('value_without_dependencies').value : undefined,
            final_value: document.getElementById('final_value') && document.getElementById('final_value').value ? document.getElementById('final_value').value : undefined,
            business_process_impact: document.getElementById('business_process_impact') ? document.getElementById('business_process_impact').value : '',
            legal_requirements_impact: document.getElementById('legal_requirements_impact') ? document.getElementById('legal_requirements_impact').value : '',
            financial_losses_impact: document.getElementById('financial_losses_impact') ? document.getElementById('financial_losses_impact').value : '',
            reputation_impact: document.getElementById('reputation_impact') ? document.getElementById('reputation_impact').value : '',
            asset_cost: document.getElementById('asset_cost').value ? parseFloat(document.getElementById('asset_cost').value) : null,
            asset_cost_rating: document.getElementById('asset_cost_rating').value,
            dependency_value: document.getElementById('dependency_value').value
        };

        const assetFormData = document.getElementById('asset-form-data');
        const assetId = assetFormData.dataset.assetId;
        let requestUrl, method;

        if (assetId) {
            // Редактирование
            requestUrl = `/api/assets/${assetId}`;
            method = 'PUT';
        } else {
            // Создание
            requestUrl = '/api/assets';
            method = 'POST';
        }

        fetch(requestUrl, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        })
        .then(response => {
            if (response.ok) {
                return response.json();
            } else {
                throw new Error('Ошибка при сохранении');
            }
        })
        .then(data => {
            alert('Актив успешно сохранен');
            window.location.href = "{{ url_for('assets_list') }}";
        })
        .catch(error => {
            alert('Ошибка при сохранении актива');
            console.error('Error:', error);
        });
    });

    // Инициализация вкладок Bootstrap
    var triggerTabList = [].slice.call(document.querySelectorAll('#assetTabs button'));
    triggerTabList.forEach(function (triggerEl) {
        var tabTrigger = new bootstrap.Tab(triggerEl)

        triggerEl.addEventListener('click', function (event) {
            event.preventDefault()
            tabTrigger.show()
        })
    })

    // Инициализация видимости критериев воздействия при загрузке
    const initialCriteria = ['business_process', 'legal_requirements', 'financial_losses', 'reputation'];
    initialCriteria.forEach(function(criterion) {
        const checkbox = document.getElementById(criterion + '_criteria');
        if (checkbox) {
            toggleRiskCriteria(criterion);
        }
    });

    // Обновляем максимальные значения при изменении динамических шкал
    const damageScaleCriteriaList = ['business_process', 'legal_requirements', 'financial_losses', 'reputation'];
    damageScaleCriteriaList.forEach(function(criterion) {
        const checkbox = document.getElementById(criterion + '_criteria');
        if (checkbox) {
            checkbox.addEventListener('change', function() {
                updateDynamicScales();
                updateMaxValues();
            });
        }
    });
});

// Функция для переключения видимости критериев воздействия
function toggleRiskCriteria(criterion) {
    const checkbox = document.getElementById(criterion + '_criteria');
    const propertyRows = ['confidentiality', 'integrity', 'availability'];

    propertyRows.forEach(function(property) {
        const rowId = property + '-' + criterion.replace('_', '-');
        const row = document.getElementById(rowId);
        if (row) {
            if (checkbox && checkbox.checked) {
                row.style.display = 'table-row';
            } else {
                row.style.display = 'none';
            }
        }
    });
}

// Функция для создания динамических шкал ущерба
function createDamageScale(criterion) {
    const scalesContainer = document.getElementById('dynamic-scales-container');

    // Определяем заголовок и описание для каждого критерия
    const criterionLabels = {
        'business_process': 'нарушении функционирования бизнес-процессов',
        'legal_requirements': 'нарушении законодательных требований',
        'financial_losses': 'финансовых потерях',
        'reputation': 'негативных последствиях для репутации'
    };

    const criterionTitle = {
        'business_process': 'нарушении функционирования бизнес-процессов',
        'legal_requirements': 'нарушении законодательных требований',
        'financial_losses': 'финансовых потерях',
        'reputation': 'негативных последствиях для репутации'
    };

    const scaleTitle = `Шкала для определения величины ущерба при ${criterionLabels[criterion]}`;

    const scaleDiv = document.createElement('div');
    scaleDiv.className = 'mb-4';
    scaleDiv.id = `scale-${criterion}`;

    scaleDiv.innerHTML = `
        <h6>${scaleTitle}</h6>
        <table class="table table-bordered">
            <thead>
                <tr>
                    <th>Величина ущерба</th>
                    <th>Определение ущерба</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Минимальная</td>
                    <td><input type="text" class="form-control" name="scale_${criterion}_minimal" placeholder="Определение минимального ущерба"></td>
                </tr>
                <tr>
                    <td>Средняя</td>
                    <td><input type="text" class="form-control" name="scale_${criterion}_medium" placeholder="Определение среднего ущерба"></td>
                </tr>
                <tr>
                    <td>Высокая</td>
                    <td><input type="text" class="form-control" name="scale_${criterion}_high" placeholder="Определение высокого ущерба"></td>
                </tr>
            </tbody>
        </table>
    `;

    scalesContainer.appendChild(scaleDiv);
}

// Функция для обновления динамических шкал при изменении критериев
function updateDynamicScales() {
    const scalesContainer = document.getElementById('dynamic-scales-container');
    scalesContainer.innerHTML = ''; // Очищаем контейнер

    const criteria = ['business_process', 'legal_requirements', 'financial_losses', 'reputation'];

    criteria.forEach(function(criterion) {
        const checkbox = document.getElementById(criterion + '_criteria');
        if (checkbox && checkbox.checked) {
            createDamageScale(criterion);
        }
    });
}

// Функция для определения максимального значения ущерба
function getMaxValue(values) {
    if (values.length === 0) return '-';

    // Преобразуем значения в числа для сравнения: Н=1, С=2, В=3
    const valueMap = { 'Н': 1, 'С': 2, 'В': 3 };
    const maxValue = Math.max(...values.map(v => valueMap[v] || 0));

    // Преобразуем обратно в буквенное обозначение
    const maxValueKey = Object.keys(valueMap).find(key => valueMap[key] === maxValue);
    return maxValueKey || '-';
}

// Функция для обновления максимальных значений в таблице 8
function updateMaxValues() {
    const properties = ['confidentiality', 'integrity', 'availability'];

    properties.forEach(function(property) {
        const values = [];

        // Собираем значения для каждого критерия
        for (let i = 1; i <= 5; i++) {
            const select = document.querySelector(`select[name="${property}_criterion_${i}"]`);
            if (select && select.value) {
                values.push(select.value);
            }
        }

        // Определяем максимальное значение
        const maxValue = getMaxValue(values);

        // Обновляем отображение максимального значения
        const maxValueElement = document.getElementById(`${property}-max-value`);
        if (maxValueElement) {
            maxValueElement.textContent = maxValue;
        }
    });
}

// Обновляем шкалы при изменении чекбоксов критериев
const criteriaCheckboxes = ['business_process', 'legal_requirements', 'financial_losses', 'reputation'];
criteriaCheckboxes.forEach(function(criterion) {
    const checkbox = document.getElementById(criterion + '_criteria');
    if (checkbox) {
        checkbox.addEventListener('change', function() {
            updateDynamicScales();
            updateMaxValues();
        });
    }
});

// Добавляем обработчики изменений для всех select в таблице 8
document.addEventListener('DOMContentLoaded', function() {
    const properties = ['confidentiality', 'integrity', 'availability'];

    properties.forEach(function(property) {
        for (let i = 1; i <= 5; i++) {
            const select = document.querySelector(`select[name="${property}_criterion_${i}"]`);
            if (select) {
                select.addEventListener('change', updateMaxValues);
            }
        }
    });

    updateDynamicScales();
    updateMaxValues(); // Инициализация при загрузке
});