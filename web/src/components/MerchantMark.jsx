const assets = { SHOPEE:'shopee', TIKTOK_SHOP:'tiktok', GRAB:'grab' }
const words = { LAZADA:'L', TIKI:'tiki', HIGHLANDS:'H' }
export default function MerchantMark({ id }) {
  return <span className={`merchant-mark mark-${id?.toLowerCase()}`} aria-hidden="true">{assets[id] ? <img src={`${import.meta.env.BASE_URL}merchants/${assets[id]}.svg`} alt=""/> : <span>{words[id] || id?.slice(0,1) || '—'}</span>}</span>
}
