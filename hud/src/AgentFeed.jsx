/* AgentFeed.jsx — JARVIS MKIII
   Live feed of agent router activity.
   Shows which agent is handling each request in real time. */

import { useState, useEffect, useRef } from 'react'

const AGENT_COLORS = {
  default: '#00D4FF',
  search:  '#8B5CF6',
  code:    '#10B981',
  file:    '#F59E0B',
  browser: '#EF4444',
  memory:  '#EC4899',
  router:  '#94A3B8',
}

const AGENT_ICONS = {
  default: 'SYS',
  search:  'SRC',
  code:    'COD',
  file:    'FIL',
  browser: 'BRS',
  memory:  'MEM',
  router:  'RTE',
}

export default function AgentFeed() {
  const [events, setEvents] = useState([])
  const [ws, setWs]         = useState(null)
  const bottomRef           = useRef(null)

  useEffect(() => {
    const socket = new WebSocket('ws://localhost:8000/ws')

    socket.onmessage = (e) => {
      const msg = e.data
      if (msg.startsWith('agent:')) {
        const parts = msg.split(':')
        const agent = parts[1] || 'default'
        const text  = parts.slice(2).join(':')
        addEvent(agent, text)
      }
      if (msg.startsWith('scheduler:alert:')) {
        const parts = msg.split(':')
        const name  = parts[2] || 'scheduler'
        const text  = parts.slice(3).join(':')
        addEvent('scheduler', text, true)
      }
    }

    setWs(socket)
    return () => socket.close()
  }, [])

  const addEvent = (agent, text, isAlert = false) => {
    const now = new Date().toLocaleTimeString('en-GB', {
      hour: '2-digit', minute: '2-digit', second: '2-digit'
    })
    setEvents(prev => [
      ...prev.slice(-19),   // keep last 20
      { agent, text, time: now, isAlert, id: Date.now() }
    ])
  }

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [events])

  // Add some demo events on mount
  useEffect(() => {
    addEvent('router', 'Agent router online — 6 agents active')
    addEvent('default', 'JARVIS MKIII operational')
  }, [])

  return (
    <div style={styles.panel}>
      <div style={styles.header}>
        AGENT FEED
        <span style={styles.count}>{events.length}</span>
      </div>

      <div style={styles.feed}>
        {events.length === 0 && (
          <div style={styles.empty}>Awaiting agent activity...</div>
        )}
        {events.map(ev => (
          <div key={ev.id} style={{
            ...styles.event,
            borderLeft: `2px solid ${AGENT_COLORS[ev.agent] || '#94A3B8'}`,
            background: ev.isAlert ? 'rgba(239,68,68,0.08)' : 'transparent',
          }}>
            <span style={styles.time}>{ev.time}</span>
            <span style={{
              ...styles.tag,
              color: AGENT_COLORS[ev.agent] || '#94A3B8',
            }}>
              {AGENT_ICONS[ev.agent] || ev.agent.toUpperCase().slice(0,3)}
            </span>
            <span style={styles.text}>{ev.text}</span>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}

const styles = {
  panel: {
    background:  'rgba(8, 12, 24, 0.85)',
    border:      '1px solid rgba(0, 212, 255, 0.25)',
    padding:     '10px 12px',
    fontFamily:  '"Courier New", monospace',
    fontSize:    9,
    color:       '#E2E8F0',
    minWidth:    220,
    maxWidth:    320,
  },
  header: {
    color:         '#00D4FF',
    fontSize:      11,
    fontWeight:    700,
    letterSpacing: 2,
    marginBottom:  8,
    display:       'flex',
    alignItems:    'center',
    justifyContent:'space-between',
  },
  count: {
    background:   'rgba(0,212,255,0.15)',
    color:        '#00D4FF',
    padding:      '1px 6px',
    borderRadius: 2,
    fontSize:     9,
  },
  feed: {
    maxHeight:  180,
    overflowY:  'auto',
    display:    'flex',
    flexDirection: 'column',
    gap:        2,
  },
  event: {
    display:    'flex',
    gap:        6,
    padding:    '3px 6px',
    alignItems: 'flex-start',
  },
  time: {
    color:     '#4A5568',
    flexShrink: 0,
    fontSize:   8,
    marginTop:  1,
  },
  tag: {
    fontWeight:  700,
    flexShrink:  0,
    fontSize:    8,
    marginTop:   1,
    letterSpacing: 1,
  },
  text: {
    color:    '#94A3B8',
    fontSize: 9,
    lineHeight: 1.4,
  },
  empty: {
    color:   '#4A5568',
    fontSize: 9,
    padding: '4px 0',
  },
}
