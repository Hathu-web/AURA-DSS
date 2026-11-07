import { Link } from 'react-router-dom'
import Icon from './Icon'
import { Card, Chart } from './ui'

export function StoryIntro({step,title,children,badge,action}) {
  return <section className="story-intro"><div><span className="story-stage">{step}</span><h2>{title}</h2><p>{children}</p></div><div className="story-intro-side">{badge&&<span className="source-chip">{badge}</span>}{action}</div></section>
}
export function FlowCard({title,sub,icon='chart',action,children,className=''}) {
  return <Card className={`flow-card ${className}`}><div className="flow-card-heading"><span className="flow-icon"><Icon name={icon} size={19}/></span><div><h3>{title}</h3>{sub&&<p>{sub}</p>}</div>{action&&<div className="flow-card-action">{action}</div>}</div>{children}</Card>
}
export function Metric({label,value,note,icon='chart',tone='purple',className=''}) {
  return <div className={`flow-metric tone-${tone} ${className}`}><span className="flow-icon"><Icon name={icon}/></span><div><span>{label}</span><strong>{value}</strong>{note&&<small>{note}</small>}</div></div>
}
export function EvidenceNote({children,title,tone=''}) {return <div className={`evidence-note ${tone}`}><Icon name="info" size={17}/><div>{title&&<b>{title}</b>}{children}</div></div>}
export function StepHeading({number,title,children}) {return <div className="step-heading"><span>{number}</span><div><h2>{title}</h2>{children&&<p>{children}</p>}</div></div>}
export function NextAction({to,title,children,label='Tiếp tục'}) {return <div className="workflow-next"><div><b>{title}</b>{children&&<p>{children}</p>}</div><Link className="btn primary" to={to}>{label}<Icon name="arrow" size={15}/></Link></div>}
export function FlowChart({option,height=270,onEvents,label}) {return <div className="flow-chart" role="img" aria-label={label}><Chart option={{...option,textStyle:{fontFamily:'Inter, Segoe UI, Arial, sans-serif',...option.textStyle}}} height={height} onEvents={onEvents}/></div>}
export function DetailPanel({title,children,open=false}) {return <details className="detail-panel" open={open||undefined}><summary>{title}</summary><div>{children}</div></details>}
