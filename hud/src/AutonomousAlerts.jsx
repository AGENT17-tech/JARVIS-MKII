/* AutonomousAlerts.jsx — JARVIS MKIII
   Proactive toast alerts fired by the autonomous scheduler.
   Appears when JARVIS acts without being asked. */

import { useState, useEffect } from 'react'

const PRIORITY_COLORS = {
  critical: { bg: 'rgba(239,68,68,0.12)',  border: '#EF4444', text: '#FCA5A5' },
  high:     { bg: 'rgba(245,158,11,0.12)', border: '#F59E0B', text: '#FCD34D' },
  medium:   { bg: 'rgba(0,212,255,0.10)',  border: '#00D4FF', text: '#67E8F9' },
  low:      { bg: 'rgba(139,92,246,0.10)', border: '#8B5CF6', text: '#C4B5FD' },
}

const ALERT_PRIORITY = {
  'alert.thermal_critical':  'critical',
  'alert.urgent_email':      'high',
  'alert.exam_approaching':  'high',
  'alert.github_inactive':   'medium',
  'alert.buc_announcement':  'medium',
  'briefing.morning':        'low',
  'briefing.evening':        'low',
  'suggest.phantom_zero_mission': 'low',
}

export default function AutonomousAlerts() {
  const [alerts, setAlerts] = useState([])

  useEffect(() => {
    const socket = new WebSocket('ws://localhost:8000/ws')

    socket.onmessage = (e) => {
      const msg = e.data
      if (msg.startsWith('scheduler:alert:')) {
        const parts    = msg.split(':')
        const action   = parts[2] || ''
        const text     = parts.slice(3).join(':')
        const priority = ALERT_PRIORITY[action] || 'medium'

        const alert = {
          id:       Date.now(),
          text,
          action,
          priority,
          time:     new Date().toLocaleTimeString('en-GB', {
            hour: '2-digit', minute: '2-digit'
          }),
        }

        setAlerts(prev => [alert, ...prev.slice(0, 4)])

        // Auto-dismiss after 8 seconds
        setTimeout(() => {
          setAlerts(prev => prev.filter(a => a.id !== alert.id))
        }, 8000)
      }
    }

    return () => socket.close()
  }, [])

  const dismiss = (id) => {
    setAlerts(prev => prev.filter(a => a.id !== id))
  }

  if (alerts.length === 0) return null

  return (
    <div style={styles.container}>
      {alerts.map(alert => {
        const clr = PRIORITY_COLORS[alert.priority] || PRIORITY_COLORS.medium
        return (
          <div key={alert.id} style={{
            ...styles.alert,
            background:  clr.bg,
            borderLeft:  `3px solid ${clr.border}`,
          }}>
            <div style={styles.alertTop}>
              <span style={{ ...styles.priority, color: clr.border }}>
                {alert.priority.toUpperCase()}
              </span>
              <span style={styles.time}>{alert.time}</span>
              <button
                onClick={() => dismiss(alert.id)}
                style={styles.dismiss}
              >✕</button>
            </div>
            <div style={{ ...styles.alertText, color: clr.text }}>
              {alert.text}
            </div>
          </div>
        )
      })}
    </div>
  )
}

const styles = {
  container: {
    position:      'fixed',
    top:           20,
    right:         20,
    display:       'flex',
    flexDirection: 'column',
    gap:           8,
    zIndex:        1000,
    maxWidth:      320,
  },
  alert: {
    padding:    '10px 12px',
    fontFamily: '"Courier New", monospace',
    fontSize:   10,
    animation:  'slideIn 0.3s ease',
  },
  alertTop: {
    display:        'flex',
    alignItems:     'center',
    gap:            8,
    marginBottom:   4,
  },
  priority: {
    fontSize:      9,
    fontWeight:    700,
    letterSpacing: 1,
  },
  time: {
    color:    '#4A5568',
    fontSize: 9,
    flex:     1,
  },
  dismiss: {
    background: 'none',
    border:     'none',
    color:      '#4A5568',
    cursor:     'pointer',
    fontSize:   10,
    padding:    0,
  },
  alertText: {
    lineHeight: 1.5,
    fontSize:   10,
  },
}
