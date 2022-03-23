## Проект Foodgram
Проект Foodgram позволяет пользователям публиковать рецепты, добавлять рецепты в избранное и список покупок, 
подписыватся на других пользователей и скачивать список продуктов.

## Технологии
- Python
- Django Rest Framework
- Docker
- postgresql
- nginx
- gunicorn

## Начало работы

Клонируйте репозиторий на локальную машину и перейдите в созданную папку.
```
git clone https://github.com/Minibaev/foodgram-project-react.git && cd foodgram-project-react/
```

### Подготовка развертывания приложения

Для работы с проектом в контейнерах должен быть установлен Docker и docker-compose.  


### Развертывание приложения

1. Необходимо запустить сборку контейнеров
```
cd infra/ && docker-compose up -d --build
```
2. Необходимо выполнить миграции и собрать статику приложения, для этого запустите скрипт
```
docker exec -ti minibaev_backend_1 python manage.py migrate
```
3. Для использования панели администратора по адресу http://localhost/admin/ необходимо создать суперпользователя.
```
docker exec -it minibaev_backend_1 python manage.py createsuperuser
```

Оживший из этого кода сайт живет [здесь](http://51.250.16.52/admin/)

## Технологии используемые в проекте
Python, Django, Django REST Framework, PostgreSQL, Nginx, Docker
