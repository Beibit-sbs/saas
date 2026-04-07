# LDAP Unavailable

## Проверить

1. Открыть `/health/deep` и проверить `ldap.status`.
2. Посмотреть список `providers` в `ldap.details`.
3. Определить: down у всех provider или у одного.

## Отличить outage от config problem

1. Если ошибка `missing bind password` или пустой `bind_dn` — это config issue.
2. Если `connection refused`, `timeout`, `socket` — это outage или сеть.
3. Если bind проходит, но search preview не проходит — проблема не в connectivity, а в search/filter config.

## Действия

1. Проверить host, port, SSL, bind DN.
2. Проверить bind отдельно сервисной учеткой.
3. Проверить сетевую доступность LDAP/AD с backend host.
4. После исправления выполнить:
   - `/health/deep`
   - pilot login для одного преподавателя
   - pilot login для одного сотрудника деканата

## Что логировать

1. Какой provider упал.
2. Тип ошибки: config / bind / network / timeout.
3. Время восстановления login flow.