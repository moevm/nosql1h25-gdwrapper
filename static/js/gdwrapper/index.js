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
    document.getElementById('commentInput').textContent     = data.comment;
    document.getElementById('saveCommentBtn').setAttribute('document_id', data.id);

}


async function createOrUpdateComment(btn){
    const document_google_id = btn.getAttribute('document_id');
    const commentInput = document.getElementById('commentInput');
    var text = commentInput.value.trim(); 
    const response = await fetch('comment/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Accept': 'application/json'
        },
        body: JSON.stringify({
            'document_google_id': document_google_id,
            'comment_text': text
        })
    });
    const data = await response.json();
    if(response.ok){
        alert('Комментарий успешно добавлен', 'success');
        window.location.reload();
    }
    else{
        alert(data.error);
    }
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
    const toast = document.createElement('div');
    toast.className = 'position-fixed bottom-0 end-0 p-3';
    toast.innerHTML = `
        <div class="toast show align-items-center text-white bg-primary" role="alert">
            <div class="d-flex">
                <div class="toast-body">
                    <div class="spinner-border spinner-border-sm me-2"></div>
                    Подготовка JSON файла...
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    document.body.appendChild(toast);
    
    const link = document.createElement('a');
    link.href = "export_data";
    link.style.display = 'none';
    document.body.appendChild(link);
    link.click();
    
    setTimeout(() => {
        toast.remove();
        link.remove();
    }, 3000);
}

async function importData() {
    const fileInput = document.getElementById('importFile');
    const errorDiv = document.getElementById('importError');
    const importBtn = document.getElementById('importBtn');
    const spinner = document.getElementById('importSpinner');
    const importModal = bootstrap.Modal.getInstance(document.getElementById('importModal'));

    errorDiv.classList.add('d-none');
    errorDiv.textContent = '';
    importBtn.disabled = true;
    spinner.classList.remove('d-none');

    try {
        if (!fileInput.files || fileInput.files.length === 0) {
            throw new Error('Выберите файл для импорта');
        }

        const file = fileInput.files[0];
        if (!file.name.toLowerCase().endsWith('.json')) {
            throw new Error('Требуется файл в формате JSON');
        }

        const formData = new FormData();
        formData.append('file', file);
        formData.append('csrfmiddlewaretoken', getCookie('csrftoken'));

        console.log(formData);

        const response = await fetch("/import_data/", {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });

        const data = await response.json();
        
        if (!response.ok) {
            if (response.status === 207) {
                showToast(
                    `Обработано ${data.total_processed} документов. Успешно: ${data.imported + data.updated}, с ошибками: ${data.error_count}`,
                    'warning'
                );
                errorDiv.textContent = `Примеры ошибок: ${data.sample_errors?.join('; ') || 'нет'}`;
                errorDiv.classList.remove('d-none');
            } else {
                throw new Error(data?.error || `Ошибка сервера: ${response.status}`);
            }
        } else {
            showToast(
                `Успешно импортировано ${data.imported} документов, обновлено ${data.updated} из ${data.total_processed}`,
                'success'
            );
            importModal.hide();
            setTimeout(() => window.location.reload(), 1500);
        }

    } catch (error) {
        console.error('Import error:', error);
        showError(error.message);
    } finally {
        importBtn.disabled = false;
        spinner.classList.add('d-none');
    }
}

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