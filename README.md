# paper_pls API

API-приложение для управления постами. / API application for managing posts.

------------------------------------

## Стек / Stack

- Python 3.11
- FastAPI
- SQLAlchemy
- Pydantic
- PostgreSQL
- Redis
- Docker / Docker Compose

------------------------------------

## Функциональность / Functionality
- Слоистая архитектура: / Layered architecture:
    - `api` - маршруты FastAPI / FastAPI routes
    - `application` - бизнес-логика / business logic
    - `domain` - бизнес-сущности / business entities
    - `infrastructure` - реализации БД / infrastructure - database
    - `scripts` - утилиты / utilities

- Точки входа: / Entry points:
  - получение поста по ID / getting a post by ID
  - получение всех постов / getting all posts
  - создание поста / creating a post
  - обновление поста / post update
  - удаление поста / deleting post

------------------------------------

## Требования / Requirements
- Docker
- Docker Compose

------------------------------------


## Установка и запуск / Installation and launch

## 1. Клонировать репозиторий / Clone the repository

```bash
git clone https://github.com/mindrusher/paper_pls.git
cd paper_pls
```

## 2. Собрать и запустить контейнеры / Build and launch containers

```bash
docker-compose up --build
```

## 2. Документация API (Swagger UI) / API documentation (Swagger UI)

http://localhost:8000/docs

## 3. Остановка контейнеров / Stopping containers

```bash
docker-compose down -v
docker-compose up --build
```

------------------------------------

### Дополнительная информация / Additional information

В проекте используются seeds - тестовые данные загрузятся автоматически при сборке контейнера
The project uses seeds - test data will be loaded automatically when building the container
