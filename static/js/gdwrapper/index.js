// Обработчик для кнопок "Подробная информация"
document.querySelectorAll('.details-btn').forEach(button => {
    button.addEventListener('click', function() {
        const row = this.closest('tr');
        const cells = row.querySelectorAll('td');
        
        // Заполняем модальное окно данными из строки таблицы
        document.getElementById('detailFileName').textContent = cells[1].textContent;
        document.getElementById('detailFileType').textContent = cells[2].textContent;
        document.getElementById('detailFileSize').textContent = cells[3].textContent;
        
        // Пример дополнительных данных (можно заменить на реальные данные)
        document.getElementById('detailFileCreated').textContent = cells[4].textContent + ' 00:00:00';
        document.getElementById('detailFileModified').textContent = cells[4].textContent + ' 00:00:00';
        document.getElementById('detailFileOwner').textContent = 'Иванов Иван';
        document.getElementById('detailFilePermissions').textContent = 'Чтение и запись';
        document.getElementById('detailFileAdditional').textContent = 
            `Файл ${cells[1].textContent} содержит важную информацию о проекте.`;
    });
});