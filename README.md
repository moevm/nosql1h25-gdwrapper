# Тема курсовой
## Сервис обёртка вокруг Google Drive API, упрощающий произведение массовых манипуляций с файлами и сбор/анализ статистики

Многостраничный сайт:

- [ ] главная страница:
  - [ ] страница с отображением всех файлов
  - [ ] поиском
  - [ ] сортировкой (дата изменения, тип файла, название)
  - [ ] фильтрацией (тип файла, дата изменения/создания от и до, наличие доступа у пользователей, типу доступа, размеру)
  - [ ] для массово выбранных файлов доступно удаление

- [ ] страница массового импорта/экспорта - позволяет скачать всё или массово загрузить некоторый набор файлов

- [ ] страница со статистикой
  - позволяет выбрать 2 параметра, которые будут отложены по осям (например тип файла и размер) и далее будет строиться визуальное отображение данных (предполагается график или столбчатая диаграмма, в зависимости от дискретности данных параметров, которые будут выбраны) (для данного примера столбчатая диаграмма, тк тип файла - дискретный параметр)

- [ ] Как обговорили в предыдущих письмах, авторизация (через гугл аккаунт) на данный момент не делается, реализуется работа с открытой на чтение папкой

## Use-case

![Use-case](ui_mockup.jpg)

![Редактировать](https://www.figma.com/design/244ALclVkmHAnxmEke1yF1/Figma-basics?node-id=1669-162202&t=RmTQcVl8X5wwRf3z-1)

## Предварительная проверка заданий

<a href=" ./../../../actions/workflows/1_helloworld.yml" >![1. Согласована и сформулирована тема курсовой]( ./../../actions/workflows/1_helloworld.yml/badge.svg)</a>

<a href=" ./../../../actions/workflows/2_usecase.yml" >![2. Usecase]( ./../../actions/workflows/2_usecase.yml/badge.svg)</a>

<a href=" ./../../../actions/workflows/3_data_model.yml" >![3. Модель данных]( ./../../actions/workflows/3_data_model.yml/badge.svg)</a>

<a href=" ./../../../actions/workflows/4_prototype_store_and_view.yml" >![4. Прототип хранение и представление]( ./../../actions/workflows/4_prototype_store_and_view.yml/badge.svg)</a>

<a href=" ./../../../actions/workflows/5_prototype_analysis.yml" >![5. Прототип анализ]( ./../../actions/workflows/5_prototype_analysis.yml/badge.svg)</a> 

<a href=" ./../../../actions/workflows/6_report.yml" >![6. Пояснительная записка]( ./../../actions/workflows/6_report.yml/badge.svg)</a>

<a href=" ./../../../actions/workflows/7_app_is_ready.yml" >![7. App is ready]( ./../../actions/workflows/7_app_is_ready.yml/badge.svg)</a>
