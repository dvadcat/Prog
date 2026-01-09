# Руководство по развёртыванию в Docker

## Требования
- Docker
- Docker Compose

## Быстрый запуск

```bash
# Сборка и запуск
docker-compose up -d --build

# Приложение доступно по адресу
http://localhost:5000
```

## Команды

```bash
# Запуск
docker-compose up -d

# Остановка
docker-compose down

# Просмотр логов
docker-compose logs -f

# Пересборка после изменений
docker-compose up -d --build
```

## Данные

База данных сохраняется в папке `instance/` и не теряется при перезапуске контейнера.

## Для Linux сервера

1. Установите Docker:
```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
```

2. Установите Docker Compose:
```bash
sudo apt install docker-compose
```

3. Скопируйте проект на сервер и запустите:
```bash
cd /path/to/project
docker-compose up -d --build
```

## Порт

По умолчанию порт 5000. Для изменения отредактируйте `docker-compose.yml`:
```yaml
ports:
  - "8080:5000"  # внешний:внутренний
```
