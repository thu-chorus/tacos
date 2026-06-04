const memoryCache = new Map()
const pendingRequests = new Map()

export const CACHE_TTL = {
  PROFILE: 5 * 60 * 1000,
  DETAIL: 2 * 60 * 1000,
  LIST: 30 * 1000
}

function cloneValue(value) {
  if (value === null || value === undefined) {
    return value
  }
  try {
    return structuredClone(value)
  } catch {
    try {
      return JSON.parse(JSON.stringify(value))
    } catch {
      return value
    }
  }
}

export function normalizeCacheKey(value) {
  if (value === null || value === undefined) {
    return ''
  }
  if (typeof value !== 'object') {
    return String(value)
  }
  if (Array.isArray(value)) {
    return `[${value.map(item => normalizeCacheKey(item)).join(',')}]`
  }
  return Object.keys(value)
    .sort()
    .map(key => `${key}:${normalizeCacheKey(value[key])}`)
    .join('|')
}

export async function getCached(cacheKey, fetcher, options = {}) {
  const ttl = Number(options.ttl ?? CACHE_TTL.DETAIL)
  const now = Date.now()
  if (options.force) {
    memoryCache.delete(cacheKey)
  }
  const cached = memoryCache.get(cacheKey)

  if (!options.force && cached && cached.expiresAt > now) {
    return cloneValue(cached.value)
  }

  if (!options.force && pendingRequests.has(cacheKey)) {
    return pendingRequests.get(cacheKey).then(cloneValue)
  }

  const pending = Promise.resolve()
    .then(fetcher)
    .then(value => {
      if (pendingRequests.get(cacheKey) === pending) {
        memoryCache.set(cacheKey, {
          value: cloneValue(value),
          expiresAt: Date.now() + ttl
        })
      }
      return value
    })
    .finally(() => {
      if (pendingRequests.get(cacheKey) === pending) {
        pendingRequests.delete(cacheKey)
      }
    })

  pendingRequests.set(cacheKey, pending)
  return pending.then(cloneValue)
}

export function invalidateCache(cacheKey) {
  memoryCache.delete(cacheKey)
  pendingRequests.delete(cacheKey)
}

export function invalidateCachePrefix(prefix) {
  ;[memoryCache, pendingRequests].forEach(cacheMap => {
    Array.from(cacheMap.keys()).forEach(key => {
      if (String(key).startsWith(prefix)) {
        cacheMap.delete(key)
      }
    })
  })
}

export function clearRequestCache() {
  memoryCache.clear()
  pendingRequests.clear()
}
