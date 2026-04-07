# Redis Unavailable

## Симптомы

1. `/health/ready` показывает `redis.status=down`.
2. `/metrics` отдает `redis_latency_seconds NaN`.
3. Могут деградировать revocation, rate limit, runtime heartbeat.

## Влияние

1. Readiness становится false.
2. Deep health теряет worker/scheduler truthfulness.
3. Auth и SRE сигналы становятся менее надежными.

## Действия

1. Проверить процесс Redis и порт.
2. Перезапустить Redis.
3. Проверить `PING` вручную.
4. Проверить `/health/ready`.
5. Проверить, что worker heartbeat снова обновляется через `/health/deep`.

## Что логировать

1. Время недоступности Redis.
2. Причину: process down / timeout / auth error.
3. Время возврата `redis.status=up`.