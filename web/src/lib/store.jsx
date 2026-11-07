import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { get } from './api'
import { dateStr, addDays } from './fmt'
const Ctx = createContext(null)
export const PRESETS = [{ k:'7', l:'7 ngày' }, { k:'30', l:'30 ngày' }, { k:'90', l:'90 ngày' }, { k:'all', l:'Tất cả' }]
export function StoreProvider({ children }) {
  const [health, setHealth] = useState(null)
  const [preset, setPreset] = useState('30')
  const [custom, setCustom] = useState({ d_from: '', d_to: '' })
  useEffect(() => { get('health').then(setHealth).catch(e => setHealth({ error: e.message })) }, [])
  const range = useMemo(() => {
    if (preset === 'custom') return custom
    if (preset === 'all') return { d_from: '', d_to: '' }
    const end = health?.data_to ? new Date(health.data_to + 'T12:00:00') : new Date()
    return { d_from: dateStr(addDays(end, -Number(preset) + 1)), d_to: dateStr(end) }
  }, [preset, custom, health])
  return <Ctx.Provider value={{ health, preset, setPreset, custom, setCustom, range }}>{children}</Ctx.Provider>
}
export const useStore = () => useContext(Ctx)
export function useApi(path, params, deps = []) {   // simple fetch hook
  const [state, set] = useState({ loading: true })
  useEffect(() => { let on = true; set(s => ({ ...s, loading: true }))
    get(path, params).then(d => on && set({ data: d, loading: false })).catch(e => on && set({ error: e.message, loading: false }))
    return () => { on = false } }, deps) // eslint-disable-line
  return state
}
