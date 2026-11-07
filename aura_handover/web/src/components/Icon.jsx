export default function Icon({ name = 'spark', size = 20 }) {
  const p = {
    home: 'M3 10 12 3 21 10V21H15V14H9V21H3Z',
    chart: 'M4 4V20H21M8 15V11M12 15V7M16 15V9M20 15V5',
    user: 'M8 7a4 4 0 1 0 8 0 4 4 0 1 0-8 0M4 21v-2a8 8 0 0 1 16 0v2',
    wallet: 'M20 8V5a2 2 0 0 0-2-2L5 6a2 2 0 0 0-2 2v11a2 2 0 0 0 2 2h15V8H5M20 12h-6v5h6m-3-3h.01',
    shield: 'm12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6ZM12 8v5m0 3h.01',
    spark: 'm12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5Z',
    check: 'm5 12 4 4L19 6',
    file: 'M14 3H5v18h14V8Zm0 0v5h5M8 12h8m-8 4h6',
    upload: 'M12 16V3m-5 5 5-5 5 5M4 16v5h16v-5',
    coins: 'M4 5a8 3 0 1 0 16 0 8 3 0 1 0-16 0v6c0 4 16 4 16 0V5M4 11v7c0 4 16 4 16 0v-7',
    swap: 'M4 7h16m-4-4 4 4-4 4M20 17H4m4-4-4 4 4 4',
    arrow: 'M4 12h16m-6-6 6 6-6 6',
    calendar: 'M5 5h14a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2ZM7 3v4m10-4v4M3 11h18m-14 4h2m4 0h2',
    presentation: 'M3 3h18v13H3ZM12 16v5m-4 0 4-3 4 3M7 12l3-4 3 2 4-4',
    info: 'M3 12a9 9 0 1 0 18 0 9 9 0 1 0-18 0M12 11v6m0-10h.01',
    target: 'M3 12a9 9 0 1 0 18 0 9 9 0 1 0-18 0M7 12a5 5 0 1 0 10 0 5 5 0 1 0-10 0M12 12h.01',
  }
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={p[name] || p.spark}/></svg>
}
