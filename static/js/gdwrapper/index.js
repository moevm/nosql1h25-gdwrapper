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