# 🔐 Настройка Service Account для Google Sheets

## Проблема
Google Sheets API требует OAuth2 аутентификации через Service Account, а не простого API ключа.

## Решение: Создание Service Account

### Шаг 1: Создайте Service Account

1. Перейдите в [Google Cloud Console](https://console.cloud.google.com/)
2. Выберите проект `sublime-seat-428918-u9`
3. Перейдите в **APIs & Services** → **Credentials**
4. Нажмите **Create Credentials** → **Service Account**
5. Заполните форму:
   - **Service account name**: `aurora-bot-sheets`
   - **Service account ID**: `aurora-bot-sheets`
   - **Description**: `Service account for Aurora bot Google Sheets integration`
6. Нажмите **Create and Continue**
7. Пропустите роли (нажмите **Continue**)
8. Нажмите **Done**

### Шаг 2: Создайте ключ для Service Account

1. В списке Service Accounts найдите созданный аккаунт
2. Нажмите на него
3. Перейдите на вкладку **Keys**
4. Нажмите **Add Key** → **Create new key**
5. Выберите **JSON**
6. Нажмите **Create**
7. Скачается файл JSON с ключом

### Шаг 3: Настройте доступ к таблице

1. Откройте [Google Sheets](https://docs.google.com/spreadsheets/d/1d9O9TOEUe0iUtN08HOBAIG_F3HV1qP5kfjHpt3gJLDc/edit)
2. Нажмите **Share** (Поделиться)
3. Добавьте email Service Account (найдите в скачанном JSON файле в поле `client_email`)
4. Дайте права **Editor**
5. Сохраните

### Шаг 4: Обновите код (альтернативный подход)

Если Service Account сложно настроить, можно использовать более простой подход с публичным доступом к таблице:

1. Откройте таблицу
2. Нажмите **Share** → **Anyone with the link** → **Editor**
3. Сохраните

### Шаг 5: Тестирование

После настройки перезапустите бота:
```bash
python bot.py
```

В логах должно появиться:
- `✅ Google Sheets интеграция подключена`
- `✅ Вопрос сохранен в Google Sheets`

## Альтернативное решение

Если Service Account сложно настроить, можно временно отключить Google Sheets логирование и использовать локальное логирование в файл.

## Проверка работы

1. Отправьте боту несколько вопросов
2. Проверьте логи на наличие сообщений о сохранении
3. Откройте Google Sheets и проверьте, появились ли записи в колонке A







