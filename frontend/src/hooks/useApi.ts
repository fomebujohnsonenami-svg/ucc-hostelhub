import { useCallback, useEffect, useState } from 'react'
import { apiRequest } from '../services/api'

export function useApi<T>(path?: string, token?: string, interval?: number) {
  const [value, setValue] = useState<{ path?: string; token?: string; data?: T; error?: Error }>({})
  const [revision, setRevision] = useState(0)
  const refresh = useCallback(() => setRevision(value => value + 1), [])
  useEffect(() => {
    if (!path) return
    const controller = new AbortController()
    let timer: number | undefined
    async function fetchData() {
      try {
        const data = await apiRequest<T>(path!, { signal: controller.signal }, token)
        if (!controller.signal.aborted) setValue({ path, token, data })
      } catch (error) {
        if (!controller.signal.aborted) setValue(previous => ({
          path, token, error: error instanceof Error ? error : new Error('Request failed'),
          data: previous.path === path && previous.token === token ? previous.data : undefined,
        }))
      } finally {
        if (interval && !controller.signal.aborted) timer = window.setTimeout(fetchData, interval)
      }
    }
    void fetchData()
    return () => { controller.abort(); window.clearTimeout(timer) }
  }, [path, token, interval, revision])
  const current = value.path === path && value.token === token ? value : {}
  return { ...current, loading: Boolean(path && !current.data && !current.error), refresh }
}
