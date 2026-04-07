# Login Failures Spike

## Возможные причины

1. LDAP/AD outage.
2. Неверный mapping групп в identity.
3. Массовый wrong password.
4. Ошибка tenant/provider policy.

## Шаги диагностики

1. Проверить alert `auth.login.failed.spike`.
2. Открыть `/health/deep` и проверить `ldap`, `redis`, `postgresql`.
3. Проверить structured logs по `error_code`:
   - `IDENTITY_INVALID_CREDENTIALS`
   - `IDENTITY_PROVIDER_DISABLED`
   - `IDENTITY_PROVIDER_UNAVAILABLE`
   - `IDENTITY_MAPPING_EMPTY`
4. Проверить audit для `auth.login.failed`.
5. Если преобладает `IDENTITY_MAPPING_EMPTY`, открыть identity mapping preview для реального пользователя.

## Действия

1. Если LDAP down — восстановить LDAP connectivity.
2. Если mapping сломан — исправить group-to-role mapping.
3. Если disabled provider — исправить provider policy.
4. После фикса проверить 3 последовательных успешных login.

## Что логировать

1. Когда начался spike.
2. Доминирующий `error_code`.
3. Сколько пользователей затронуто.
4. Когда spike прекратился.