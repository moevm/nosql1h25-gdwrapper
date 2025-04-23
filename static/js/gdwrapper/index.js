function getCookie(name){
  const v = `; ${document.cookie}`.split(`; ${name}=`);
  return v.length === 2 ? v.pop().split(';').shift() : undefined;
}

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

function refreshData(event){
  event.preventDefault();
  fetch(event.currentTarget.href,{
    method:'POST',
    headers:{'X-CSRFToken':getCookie('csrftoken'),'Accept':'application/json'}
  })
  .then(r=>{if(!r.ok)throw new Error();return r.json();})
  .then(()=>{alert('Данные успешно синхронизированы');location.reload();})
  .catch(()=>alert('Ошибка при синхронизации данных'));
}

function setAllFilesCheckboxes(v){
  document.querySelectorAll('.form-check-input').forEach(cb=>cb.checked=v);
}