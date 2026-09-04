import time


_cache = {}


def cache_get(key):
    """Anahtarın değerini döndürür; yoksa veya süresi
    geçmişse None döner."""

    entry = _cache.get(key)

    if entry is None:
        return None

    expires_at, value = entry

    if time.time() > expires_at:
        del _cache[key]
        return None

    return value


def cache_set(key, value, ttl_seconds: int):
    """Anahtarı belirtilen süre kadar önbelleğe alır."""

    _cache[key] = (
        time.time() + ttl_seconds,
        value
    )


def cached(ttl_seconds: int, should_cache=None):
    """
    Fonksiyon sonuçlarını önbelleğe alan decorator.

    None dönen sonuçlar önbelleğe alınmaz
    (hata durumlarının tekrar denenebilmesi için).

    should_cache verildiyse sonuç, bu fonksiyona verilip
    True döndüğünde önbelleğe alınır (ör. sadece başarılı cevaplar).
    """

    def decorator(func):

        def wrapper(*args, **kwargs):

            key = (
                f"{func.__module__}.{func.__name__}:"
                f"{args}:{sorted(kwargs.items())}"
            )

            cached_value = cache_get(key)

            if cached_value is not None:
                return cached_value

            result = func(*args, **kwargs)

            if result is not None and (should_cache is None or should_cache(result)):
                cache_set(key, result, ttl_seconds)

            return result

        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__

        return wrapper

    return decorator


def cache_stats() -> dict:
    """Önbellekteki aktif (süresi geçmemiş) kayıt sayısını döndürür."""

    now = time.time()

    active = [
        key
        for key, (expires_at, _) in _cache.items()
        if expires_at > now
    ]

    return {
        "active_entries": len(active)
    }


def cache_clear():
    """Önbelleğin tamamını temizler."""

    _cache.clear()
