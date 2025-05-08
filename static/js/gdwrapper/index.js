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


function createOrUpdateComment(btn){
    const document_google_id = btn.getAttribute('document_id');
    const commentInput = document.getElementById('commentInput');
    var text = commentInput.value.trim(); 
    fetch('comment/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Accept': 'application/json'
        },
        body: JSON.stringify({
            'document_google_id': document_google_id,
            'comment_text': text
        })
    })
    .then(response => {
        return response.json();
    })
    .then(data => { 
        alert('Комментарий успешно добавлен', 'success');
        window.location.reload();
    });
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

function toggleCheckInput(event){
    const parentItem = event.target.closest('li');
    const childCheckboxes = parentItem.querySelectorAll('input[type="checkbox"]');
    childCheckboxes.forEach(child => {
        child.checked = event.target.checked;
    });
}

function toggleTreeItem(element) {
    const icon = element.querySelector('i');
    const parentLi = element.closest('li');
    const childUl = parentLi.querySelector('ul');
    
    childUl.classList.toggle('show');
    icon.classList.toggle('fa-caret-right');
    icon.classList.toggle('fa-caret-down');
}

document.querySelectorAll('.tree-view > li').forEach(item => {
    item.querySelector('.tree-toggle')?.click();
});