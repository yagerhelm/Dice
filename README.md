# 🎲 Telegram Dice Game Bot

Многопользовательский бот для игры в кости в Telegram с системой ставок и автоматическим распределением призов.

> [!NOTE]
>## 📋 Описание
>
>Бот позволяет пользователям создавать игровые лобби для игры в кости, делать ставки и соревноваться друг с другом. Система автоматически определяет победителей и распределяет призовой фонд.
>
>### ⭐️ Основные функции
>
>- Создание игровых лобби с настраиваемым количеством игроков
>- Система ставок с внутриигровой валютой (GW)
>- Автоматическое определение победителей
>- Система комиссии (5% от призового фонда)
>- Поддержка множества активных игр одновременно
>- История игр и статистика
>- Система приглашений и регистрации пользователей

## 🎮 Команды

- `/dice [количество игроков] [ставка]` - Создать новую игру
- `/all_games` - Показать список активных игр
- `/history` - Показать историю последних игр
- `/profile` - Просмотр профиля
- `/invite [username]` - Пригласить пользователя
- `/activate` - Активировать бота в чате
- `/deactivate` - Деактивировать бота
- `/id` - Получить ID чата

## 🔒 Безопасность

- Проверка прав администратора для активации/деактивации бота
- Валидация ставок и балансов пользователей
- Защита от дублирования профилей
- Проверка активности бота в чатах

## 📊 Особенности реализации

- Асинхронная обработка всех операций
- Модульная структура кода
- Автоматическое управление состоянием игры
- Система обработки ошибок и исключений
- Поддержка множества одновременных игровых сессий

## 🎯 Игровой процесс

1. Создатель игры указывает количество игроков и ставку
2. Игроки присоединяются к лобби
3. Игра начинается автоматически при достижении максимального количества игроков
4. Каждый игрок бросает кости
5. Система определяет победителя(ей)
6. Призовой фонд распределяется между победителями за вычетом комиссии


> [!WARNING]
>## 🛠 Технические детали
>
>### Используемые библиотеки
>
>Для работы бота требуются следующие библиотеки:
>
>- **aiogram>=3.0.0** - Асинхронный фреймворк для создания Telegram ботов
>- **python-dotenv>=1.0.0** - Загрузка переменных окружения из .env файла
>- **aiosqlite>=0.19.0** - Асинхронная работа с SQLite базой данных
>- **aiofiles>=23.2.1** - Асинхронная работа с файлами
>- **asyncio>=3.4.3** - Библиотека для асинхронного программирования
>- **typing>=3.7.4.3** - Поддержка аннотаций типов
>- **sqlite3** - Встроенная библиотека для работы с SQLite
>
>### База данных
>
>SQLite с следующими таблицами:
>- `users`: Профили пользователей
>- `active_chats`: Активированные чаты
>- `game_history`: История игр

> [!CAUTION]
>## 💾 Установка и настройка
>
>1. Клонируйте репозиторий
>2. Установка зависимостей:
>```bash
>pip install -r requirements.txt
>```
>3. Создайте файл `my_token.py` и добавьте токен бота:
>```python
>TOKEN = 'ВАШ_ТОКЕН_БОТА'
>```
>4. Запустите бота:
>```bash
>python main.py
>```

> [!NOTE]  
> 
> ╭––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––╮<br />
><br />
>v1.0.0 ⬎<br />
>**`28.11.2024`**<br />
>• Создан игровой бот с работающими функциями.<br />
><br />
>v1.1.0 ⬎<br />
>**`28.11.2024`**<br />
>• Бот переписан на aiogram 3.<br />
><br />
>v1.2.0 ⬎<br />
>**`30.11.2024`**<br />
>• dice_game.py переписан под db.py по просьбе пользователя.<br />
><br />
>v1.2.1f ⬎<br />
>**`30.11.2024`**<br />
>• Фиксы и переписка БДшка.<br />
><br />
>╰––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––╯

## 📝 Лицензия

MIT License
