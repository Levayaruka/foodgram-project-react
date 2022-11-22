# foodgram
![workflow status](https://github.com/Levayaruka/foodgram-project-react/actions/workflows/main.yml/badge.svg)
### Описание
На этом сервисе пользователи смогут публиковать рецепты, подписываться на публикации других пользователей, добавлять понравившиеся рецепты в список «Избранное», а перед походом в магазин скачивать сводный список продуктов, необходимых для приготовления одного или нескольких выбранных блюд.
### IP-адрес и email:pass администратора

http://158.160.44.125/admin

admin@mail.ru:password

### Запуск
Клонировать репозиторий
`git clone https://github.com/Levayaruka/foodgram-project-react.git`

Перейти в каталог foodgram-project-react/infra/ и создать .env и заполнить по примеру
```
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
```
Развернуть проект, создать и применить миграции, создать админа, подгрузить статику и ингредиенты
```
docker-compose up -d --build
docker-compose exec web python manage.py makemigrations users
docker-compose exec web python manage.py makemigrations recipes
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py collectstatic --no-input
docker-compose exec web python manage.py ingredients
``` 
Теперь проект доступен по адресу http://127.0.0.1/recipes
