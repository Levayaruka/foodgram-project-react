https://github.com/Levayaruka/foodgram-project-react/actions/workflows/main.yml/badge.svg

# foodgram
### Описание
На этом сервисе пользователи смогут публиковать рецепты, подписываться на публикации других пользователей, добавлять понравившиеся рецепты в список «Избранное», а перед походом в магазин скачивать сводный список продуктов, необходимых для приготовления одного или нескольких выбранных блюд.
### Запуск
foodgram-project-react/infra/
создать .env
```
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
```
```
docker-compose up -d --build
docker-compose exec web python manage.py makemigrations users
docker-compose exec web python manage.py makemigrations recipes
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py collectstatic --no-input
``` 
