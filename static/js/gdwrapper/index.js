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
    $('#exportModal').modal('hide');
    
    const toast = $(`
        <div class="position-fixed bottom-0 end-0 p-3" style="z-index: 11">
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
        </div>
    `);
    
    $('body').append(toast);
    
    setTimeout(() => {
        window.location.href = "{% url 'export_data' %}";
        toast.remove();
    }, 500);
}

function importData() {
    const fileInput = document.getElementById('importFile');
    const errorDiv = document.getElementById('importError');
    const importBtn = document.getElementById('importBtn');
    const spinner = document.getElementById('importSpinner');
    
    errorDiv.classList.add('d-none');
    errorDiv.textContent = '';
    
    if (!fileInput.files.length) {
        errorDiv.textContent = 'Пожалуйста, выберите ZIP-архив';
        errorDiv.classList.remove('d-none');
        return;
    }
    
    const fileName = fileInput.files[0].name.toLowerCase();
    if (!fileName.endsWith('.zip')) {
        errorDiv.textContent = 'Файл должен быть в формате ZIP';
        errorDiv.classList.remove('d-none');
        return;
    }

    importBtn.classList.add('d-none');
    spinner.classList.remove('d-none');
    
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('csrfmiddlewaretoken', '{{ csrf_token }}');
    

    fetch("{% url 'import_data' %}", {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => Promise.reject(err));
        }
        return response.json();
    })
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        
        $('#importModal').modal('hide');
        
        const toast = $(`
            <div class="position-fixed bottom-0 end-0 p-3" style="z-index: 11">
                <div class="toast show" role="alert" aria-live="assertive" aria-atomic="true">
                    <div class="toast-header bg-success text-white">
                        <strong class="me-auto">Импорт завершен</strong>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
                    </div>
                    <div class="toast-body">
                        Успешно импортировано ${data.count} файлов
                    </div>
                </div>
            </div>
        `);
        
        $('body').append(toast);
        
        setTimeout(() => {
            location.reload();
        }, 2000);
    })
    .catch(error => {
        console.error('Import error:', error);
        errorDiv.textContent = error.message || 'Произошла ошибка при импорте';
        errorDiv.classList.remove('d-none');
    })
    .finally(() => {
        importBtn.classList.remove('d-none');
        spinner.classList.add('d-none');
    });
}