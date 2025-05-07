function showMoreInfo(btn){
  const data = JSON.parse(document.getElementById(btn.getAttribute('document_id')).textContent);
  document.getElementById('detailFileName').textContent   = data.name;
  document.getElementById('detailFileType').textContent   = data.mimeType;
  document.getElementById('detailFileSize').textContent   = data.size;
  document.getElementById('detailFileCreated').textContent  = data.createdTime;
  document.getElementById('detailFileModified').textContent = data.modifiedTime;
  document.getElementById('detailFileOwner').textContent     = data.ownerEmail;
  document.getElementById('detailFilePermissions').textContent =
      JSON.stringify(data.capabilities, null, 2);
}

function refreshData(event) {
    event.preventDefault();
    
    const url = event.currentTarget.getAttribute('href');
    
    fetch(url, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Accept': 'application/json'
        }
    })
    .then(response => {
        return response.json();
    })
    .then(data => {
        if(data.redirect_to){
            window.location.href = data.redirect_to;
        }else{
            alert('Данные успешно синхронизированы', 'success');
            window.location.reload();
        }
    });
}

function setAllFilesCheckboxes(v){
  document.querySelectorAll('.form-check-input').forEach(cb=>cb.checked=v);
}

function exportData() {
    // Получаем модальное окно без jQuery
    const exportModal = document.getElementById('exportModal');
    const modalInstance = bootstrap.Modal.getInstance(exportModal);
    
    // Закрываем модальное окно
    if (modalInstance) {
        modalInstance.hide();
    }

    // Показываем уведомление
    const toast = document.createElement('div');
    toast.className = 'position-fixed bottom-0 end-0 p-3';
    toast.innerHTML = `
        <div class="toast show" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header">
                <strong class="me-auto">Экспорт данных</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">
                <div class="spinner-border spinner-border-sm me-2"></div>
                Подготовка архива...
            </div>
        </div>
    `;
    
    document.body.appendChild(toast);

    setTimeout(() => {
        window.location.href = "export_data";
        toast.remove();
    }, 500);
}

async function importData() {
    const fileInput = document.getElementById('importFile');
    const errorDiv = document.getElementById('importError');
    const importBtn = document.getElementById('importBtn');
    const spinner = document.getElementById('importSpinner');
    const importModal = bootstrap.Modal.getInstance(document.getElementById('importModal'));

    // Сброс состояния
    errorDiv.classList.add('d-none');
    errorDiv.textContent = '';
    importBtn.disabled = true;
    spinner.classList.remove('d-none');

    try {
        // 1. Проверка файла
        if (!fileInput.files || fileInput.files.length === 0) {
            throw new Error('Выберите файл для импорта');
        }

        const file = fileInput.files[0];
        if (!file.name.toLowerCase().endsWith('.zip')) {
            throw new Error('Требуется файл в формате ZIP');
        }

        // 2. Подготовка данных
        const formData = new FormData();
        formData.append('file', file);
        formData.append('csrfmiddlewaretoken', getCookie('csrftoken'));

        // 3. Отправка запроса с таймаутом
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 секунд таймаут

        const response = await fetch("/import_data/", {
            method: 'POST',
            body: formData,
            signal: controller.signal,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        clearTimeout(timeoutId);

        // 4. Обработка ответа
        if (!response.ok) {
            const errorData = await response.json().catch(() => null);
            throw new Error(errorData?.error || `HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        
        // 5. Успешный импорт
        importModal.hide();
        showToast('Данные успешно импортированы', 'success');
        
        // 6. Принудительное обновление страницы
        setTimeout(() => {
            window.location.href = "";
        }, 1500);

    } catch (error) {
        console.error('Import error:', error);
        
        // Специальная обработка разных типов ошибок
        let errorMessage = 'Ошибка при импорте данных';
        
        if (error.name === 'AbortError') {
            errorMessage = 'Превышено время ожидания сервера';
        } else if (error.message.includes('Failed to fetch')) {
            errorMessage = 'Ошибка соединения с сервером';
        } else {
            errorMessage = error.message || error.toString();
        }

        showError(errorMessage);
    } finally {
        importBtn.disabled = false;
        spinner.classList.add('d-none');
    }
}

// Вспомогательные функции
function showError(message) {
    const errorDiv = document.getElementById('importError');
    errorDiv.textContent = message;
    errorDiv.classList.remove('d-none');
    errorDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast show position-fixed bottom-0 end-0 m-3 text-white bg-${type}`;
    toast.style.zIndex = '1100';
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 5000);
}