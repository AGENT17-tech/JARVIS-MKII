/* WorldStatePanel.jsx — JARVIS MKIII
   Live world state feed — CPU, RAM, sensors, threat level
   Drop into App.jsx and add <WorldStatePanel /> wherever you want it */

import { useState, useEffect } from 'react'

const API = 'http://localhost:8000'

const ThreatColor = { minimal: '#00D4FF', elevated: '#F59E0B', critical: '#EF4444' }

export default function WorldStatePanel() {
  const [state, setState] = useState(null)
  const [blink, setBlink]  = useState(true)

  useEffect(() => {
    const fetch_state = async () => {
      try {
        const r = await fetch(`${API}/world_state`)
        if (r.ok) setState(await r.json())
      } catch (_) {}
    }
    fetch_state()
    const iv = setInterval(fetch_state, 15000)
    return () => clearInterval(iv)
  }, [])

  useEffect(() => {
    const iv = setInterval(() => setBlink(b => !b), 800)
    return () => clearInterval(iv)
  }, [])

  if (!state) return (
    <div style={styles.panel}>
      <div style={styles.header}>WORLD STATE</div>
      <div style={styles.muted}>Initializing...</div>
    </div>
  )

  const sys      = state.system     || {}
  const email    = state.email      || {}
  const calendar = state.calendar   || {}
  const github   = state.github     || {}
  const buc      = state.buc_portal || {}
  const threat   = state.threat_level || 'minimal'
  const threatClr = ThreatColor[threat] || '#00D4FF'

  return (
    <div style={styles.panel}>
      {/* Header */}
      <div style={styles.header}>
        WORLD STATE
        <span style={{ ...styles.dot, background: blink ? '#00D4FF' : 'transparent' }} />
      </div>

      {/* System metrics */}
      <div style={styles.section}>
        <Bar label="CPU"  value={sys.cpu  || 0} color="#00D4FF" />
        <Bar label="RAM"  value={sys.ram  || 0} color="#8B5CF6" />
        <Bar label="VRAM" value={sys.gpu_vram || 0} color="#10B981" />
      </div>

      {/* Threat */}
      <div style={{ ...styles.row, marginTop: 8 }}>
        <span style={styles.label}>THREAT</span>
        <span style={{ ...styles.value, color: threatClr, fontWeight: 700 }}>
          {threat.toUpperCase()}
        </span>
      </div>

      {/* Temp + Disk */}
      <div style={styles.row}>
        <span style={styles.label}>TEMP</span>
        <span style={{ ...styles.value, color: sys.temp > 75 ? '#EF4444' : '#E2E8F0' }}>
          {sys.temp || 0}°C
        </span>
      </div>
      <div style={styles.row}>
        <span style={styles.label}>DISK</span>
        <span style={styles.value}>{sys.disk_free || '—'}</span>
      </div>

      <div style={styles.divider} />

      {/* Email */}
      <div style={styles.row}>
        <span style={styles.label}>EMAIL</span>
        <span style={{ ...styles.value, color: email.urgent > 0 ? '#EF4444' : '#E2E8F0' }}>
          {email.unread || 0} unread
          {email.urgent > 0 && ` · ${email.urgent} urgent`}
        </span>
      </div>

      {/* Calendar */}
      {calendar.next_event && (
        <div style={styles.row}>
          <span style={styles.label}>NEXT</span>
          <span style={{ ...styles.value, fontSize: 9 }}>{calendar.next_event}</span>
        </div>
      )}

      {/* GitHub */}
      <div style={styles.row}>
        <span style={styles.label}>GITHUB</span>
        <span style={{ ...styles.value, color: github.days_since > 2 ? '#F59E0B' : '#10B981' }}>
          {github.days_since === 0 ? 'committed today' : `${github.days_since}d ago`}
        </span>
      </div>

      {/* BUC */}
      {buc.next_exam && (
        <div style={styles.row}>
          <span style={styles.label}>EXAM</span>
          <span style={{ ...styles.value, color: buc.days_to_exam <= 3 ? '#EF4444' : '#F59E0B' }}>
            {buc.days_to_exam}d — {buc.next_exam}
          </span>
        </div>
      )}

      {buc.announcements > 0 && (
        <div style={styles.row}>
          <span style={styles.label}>BUC</span>
          <span style={{ ...styles.value, color: '#F59E0B' }}>
            {buc.announcements} announcement(s)
          </span>
        </div>
      )}
    </div>
  )
}

function Bar({ label, value, color }) {
  return (
    <div style={{ marginBottom: 4 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 2 }}>
        <span style={styles.label}>{label}</span>
        <span style={{ ...styles.value, color }}>{value}%</span>
      </div>
      <div style={styles.barBg}>
        <div style={{ ...styles.barFill, width: `${value}%`, background: color }} />
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
    fontSize:    10,
    color:       '#E2E8F0',
    minWidth:    180,
  },
  header: {
    color:        '#00D4FF',
    fontSize:     11,
    fontWeight:   700,
    letterSpacing: 2,
    marginBottom: 8,
    display:      'flex',
    alignItems:   'center',
    gap:          6,
  },
  dot: {
    width:        6,
    height:       6,
    borderRadius: '50%',
    display:      'inline-block',
  },
  section: { marginBottom: 6 },
  divider: {
    borderTop:    '1px solid rgba(0,212,255,0.15)',
    margin:       '6px 0',
  },
  row: {
    display:        'flex',
    justifyContent: 'space-between',
    marginBottom:   3,
    gap:            8,
  },
  label: {
    color:         '#7A8FA8',
    letterSpacing: 1,
    flexShrink:    0,
  },
  value: {
    color:     '#E2E8F0',
    textAlign: 'right',
    fontSize:  10,
  },
  muted: { color: '#7A8FA8', fontSize: 10 },
  barBg: {
    background:   'rgba(255,255,255,0.08)',
    height:       3,
    borderRadius: 2,
    overflow:     'hidden',
  },
  barFill: {
    height:       3,
    borderRadius: 2,
    transition:   'width 1s ease',
  },
}
