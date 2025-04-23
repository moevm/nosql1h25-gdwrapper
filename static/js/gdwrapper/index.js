function showMoreInfo(btn) {
    const documentString = document.getElementById(btn.getAttribute('document_id')).textContent;
    const document_ = JSON.parse(documentString);
    document.getElementById('detailFileName').textContent = document_.name;
    document.getElementById('detailFileType').textContent = document_.mimeType;
    document.getElementById('detailFileSize').textContent = document_.size;
    document.getElementById('detailFileCreated').textContent = document_.createdTime;
    document.getElementById('detailFileModified').textContent = document_.modifiedTime;
    document.getElementById('detailFileOwner').textContent = document_.ownerEmail;
    document.getElementById('detailFilePermissions').textContent = JSON.stringify(document_.capabilities, null, 2);
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


function setAllFilesCheckboxes(value){
    document.querySelectorAll('.form-check-input').forEach(checkbox => {
        checkbox.checked = value;
    });
}