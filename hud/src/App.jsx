import { useState, useEffect, useRef } from 'react'
import './App.css'
import WorldStatePanel from './WorldStatePanel'
import AgentFeed from './AgentFeed'
import AutonomousAlerts from './AutonomousAlerts'

/* ─── BOOT SEQUENCE ─────────────────────────────────────────── */
const BOOT_STEPS = [
  { key: 'scanline',   delay: 400  },
  { key: 'reactor',    delay: 900  },
  { key: 'title',      delay: 1400 },
  { key: 'corners',    delay: 1800 },
  { key: 'panelTL',    delay: 2200 },
  { key: 'panelTR',    delay: 2500 },
  { key: 'suit',       delay: 2800 },
  { key: 'worldmap',   delay: 3000 },
  { key: 'stats',      delay: 3200 },
  { key: 'panelBR',    delay: 3400 },
  { key: 'missionlog', delay: 3600 },
  { key: 'cairo',      delay: 3700 },
  { key: 'github',     delay: 3900 },
  { key: 'mkiii',      delay: 4100 },
  { key: 'ticker',     delay: 4200 },
  { key: 'ready',      delay: 4400 },
]

/* ─── WORLD MAP ──────────────────────────────────────────────── */
const WorldMap = () => {
  const canvasRef = useRef(null)
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    let frame = 0
    const W = canvas.width, H = canvas.height
    const regions = [
      { pts:[[6,8],[4,12],[4,18],[6,24],[8,28],[12,32],[16,30],[20,28],[22,22],[22,16],[18,10],[12,8],[6,8]], fill:true },
      { pts:[[2,10],[1,12],[3,14],[5,12],[4,10],[2,10]], fill:true },
      { pts:[[22,4],[20,6],[20,10],[22,12],[25,12],[26,8],[25,5],[22,4]], fill:true },
      { pts:[[12,32],[10,36],[11,40],[14,40],[16,36],[14,32],[12,32]], fill:true },
      { pts:[[16,32],[15,33],[17,34],[18,33],[16,32]], fill:false },
      { pts:[[16,40],[14,44],[14,52],[15,60],[17,66],[20,68],[22,66],[24,60],[24,52],[22,46],[20,40],[16,40]], fill:true },
      { pts:[[20,70],[19,71],[21,72],[22,71],[20,70]], fill:false },
      { pts:[[34,9],[33,11],[35,12],[37,11],[36,9],[34,9]], fill:true },
      { pts:[[39,14],[38,16],[38,20],[40,21],[41,18],[42,16],[40,14],[39,14]], fill:true },
      { pts:[[37,16],[36,17],[37,19],[38,18],[38,16],[37,16]], fill:true },
      { pts:[[38,22],[36,24],[36,28],[38,30],[40,28],[42,26],[42,22],[40,20],[38,22]], fill:true },
      { pts:[[36,24],[34,26],[34,30],[36,32],[38,30],[38,26],[36,24]], fill:true },
      { pts:[[42,8],[40,10],[40,14],[42,16],[44,14],[46,12],[46,8],[44,7],[42,8]], fill:true },
      { pts:[[40,20],[40,24],[42,26],[44,24],[46,22],[46,18],[44,16],[42,16],[40,20]], fill:true },
      { pts:[[42,26],[40,28],[40,32],[42,34],[43,32],[44,28],[43,26],[42,26]], fill:true },
      { pts:[[44,22],[42,26],[44,30],[46,30],[48,28],[48,24],[46,22],[44,22]], fill:true },
      { pts:[[46,8],[44,10],[44,18],[46,22],[48,24],[52,22],[58,18],[64,16],[68,14],[72,12],[74,10],[70,8],[60,7],[50,7],[46,8]], fill:true },
      { pts:[[46,22],[44,24],[44,28],[46,28],[48,26],[50,24],[50,22],[46,22]], fill:true },
      { pts:[[48,28],[46,30],[46,32],[48,34],[52,34],[54,32],[52,30],[50,28],[48,28]], fill:true },
      { pts:[[50,34],[48,36],[50,42],[52,44],[54,42],[56,38],[54,34],[52,34],[50,34]], fill:true },
      { pts:[[54,30],[52,32],[52,36],[54,38],[56,36],[58,34],[58,30],[56,28],[54,30]], fill:true },
      { pts:[[36,32],[34,34],[34,40],[36,44],[40,46],[44,46],[46,42],[46,36],[44,32],[40,30],[38,30],[36,32]], fill:true },
      { pts:[[36,44],[34,48],[34,56],[36,62],[38,66],[40,68],[42,66],[44,62],[46,56],[46,50],[44,46],[40,46],[36,44]], fill:true },
      { pts:[[50,42],[48,44],[50,48],[52,46],[52,42],[50,42]], fill:true },
      { pts:[[48,56],[47,58],[48,62],[49,60],[49,56],[48,56]], fill:true },
      { pts:[[54,22],[52,24],[52,28],[54,30],[58,30],[60,26],[60,22],[56,20],[54,22]], fill:true },
      { pts:[[60,30],[58,32],[58,38],[60,42],[62,44],[64,40],[64,34],[62,30],[60,30]], fill:true },
      { pts:[[62,44],[61,45],[62,46],[63,45],[62,44]], fill:false },
      { pts:[[68,28],[66,30],[66,36],[68,38],[70,36],[72,32],[70,28],[68,28]], fill:true },
      { pts:[[70,34],[68,36],[68,42],[70,44],[72,42],[72,36],[70,34]], fill:true },
      { pts:[[64,16],[62,18],[62,24],[64,28],[68,30],[72,28],[76,24],[76,18],[72,14],[68,14],[64,16]], fill:true },
      { pts:[[76,20],[74,22],[74,26],[76,26],[78,24],[78,20],[76,20]], fill:true },
      { pts:[[78,18],[77,20],[78,24],[80,22],[80,18],[78,18]], fill:true },
      { pts:[[76,34],[74,36],[75,40],[77,38],[77,34],[76,34]], fill:true },
      { pts:[[72,42],[70,44],[71,46],[74,46],[75,44],[73,42],[72,42]], fill:true },
      { pts:[[68,40],[66,42],[67,46],[69,46],[70,44],[69,40],[68,40]], fill:true },
      { pts:[[76,52],[74,54],[74,60],[76,64],[80,66],[84,64],[86,60],[84,54],[80,52],[76,52]], fill:true },
      { pts:[[88,62],[87,64],[88,66],[90,64],[89,62],[88,62]], fill:true },
      { pts:[[78,46],[76,47],[77,50],[79,50],[80,47],[78,46]], fill:true },
    ]
    const cairoX = 0.484 * W
    const cairoY = 0.42 * H
    const draw = () => {
      ctx.clearRect(0, 0, W, H); frame++
      const pulse = Math.sin(frame * 0.02) * 0.12 + 0.88
      const pulse2 = Math.sin(frame * 0.015 + 1) * 0.1 + 0.9
      ctx.strokeStyle = 'rgba(0,160,255,0.10)'; ctx.lineWidth = 0.5
      for (let x = 0; x <= W; x += W / 18) { ctx.beginPath(); ctx.moveTo(x,0); ctx.lineTo(x,H); ctx.stroke() }
      for (let y = 0; y <= H; y += H / 9) { ctx.beginPath(); ctx.moveTo(0,y); ctx.lineTo(W,y); ctx.stroke() }
      regions.forEach((reg, ri) => {
        const cP = Math.sin(frame * 0.01 + ri * 0.4) * 0.08 + 0.92
        ctx.beginPath()
        reg.pts.forEach(([px,py],i) => { const x=(px/100)*W,y=(py/100)*H; i===0?ctx.moveTo(x,y):ctx.lineTo(x,y) })
        ctx.closePath()
        if (reg.fill) { ctx.fillStyle=`rgba(0,100,200,${0.12*cP})`; ctx.fill() }
        ctx.shadowColor='rgba(0,200,255,0.5)'; ctx.shadowBlur=2
        ctx.strokeStyle=`rgba(0,200,255,${0.65*cP})`; ctx.lineWidth=0.9; ctx.stroke(); ctx.shadowBlur=0
      })
      ctx.setLineDash([2,8]); ctx.strokeStyle='rgba(0,160,255,0.08)'; ctx.lineWidth=0.5
      for (let y=H*0.1; y<H; y+=H*0.2) { ctx.beginPath(); ctx.moveTo(0,y); ctx.lineTo(W,y); ctx.stroke() }
      ctx.setLineDash([])
      const mP = Math.sin(frame*0.07)*0.5+0.5
      for (let r=1; r<=3; r++) { ctx.beginPath(); ctx.arc(cairoX,cairoY,4+mP*10*r/3,0,Math.PI*2); ctx.strokeStyle=`rgba(0,255,200,${(0.6-mP*0.4)/r})`; ctx.lineWidth=0.8; ctx.stroke() }
      ctx.shadowColor='rgba(0,255,200,0.9)'; ctx.shadowBlur=10
      ctx.beginPath(); ctx.arc(cairoX,cairoY,3,0,Math.PI*2); ctx.fillStyle='#00ffc8'; ctx.fill(); ctx.shadowBlur=0
      ctx.font='bold 8px "Share Tech Mono"'; ctx.fillStyle=`rgba(0,255,200,${0.9*pulse})`; ctx.fillText('◈ CAIRO',cairoX+8,cairoY-5)
      const cities = [{x:0.14,y:0.25,n:'NEW YORK'},{x:0.40,y:0.18,n:'LONDON'},{x:0.58,y:0.16,n:'MOSCOW'},{x:0.70,y:0.28,n:'BEIJING'},{x:0.50,y:0.55,n:'NAIROBI'},{x:0.20,y:0.55,n:'SAO PAULO'}]
      cities.forEach((city,ci) => {
        const a=Math.sin(frame*0.03+ci*1.1)*0.2+0.35, cx2=city.x*W, cy2=city.y*H
        ctx.setLineDash([3,6]); ctx.beginPath(); ctx.moveTo(cx2,cy2); ctx.lineTo(cairoX,cairoY); ctx.strokeStyle=`rgba(0,160,255,${a*0.45})`; ctx.lineWidth=0.5; ctx.stroke(); ctx.setLineDash([])
        const t=((frame*0.006+ci*0.18)%1), px=cx2+(cairoX-cx2)*t, py=cy2+(cairoY-cy2)*t
        ctx.beginPath(); ctx.arc(px,py,1.5,0,Math.PI*2); ctx.fillStyle=`rgba(0,255,200,${a*1.8})`; ctx.fill()
        ctx.beginPath(); ctx.arc(cx2,cy2,2.5,0,Math.PI*2); ctx.fillStyle=`rgba(0,210,255,${a*2})`; ctx.fill()
        ctx.font='7px "Share Tech Mono"'; ctx.fillStyle=`rgba(0,200,255,${a*1.3})`; ctx.fillText(city.n,cx2-12,cy2-6)
      })
      const scanY=((frame*1.0)%(H+20))-10
      const sg=ctx.createLinearGradient(0,scanY-10,0,scanY+10)
      sg.addColorStop(0,'rgba(0,200,255,0)'); sg.addColorStop(0.5,`rgba(0,200,255,${0.14*pulse2})`); sg.addColorStop(1,'rgba(0,200,255,0)')
      ctx.fillStyle=sg; ctx.fillRect(0,scanY-10,W,20)
      ctx.font='8px "Share Tech Mono"'; ctx.fillStyle=`rgba(0,180,255,${0.5*pulse})`
      ctx.fillText('GLOBAL NETWORK — LIVE',8,H-5); ctx.fillText(`FRAME: ${String(frame).padStart(6,'0')}`,W-100,H-5); ctx.fillText('LAT: 30.04° N  LON: 31.24° E',W/2-80,H-5)
      ctx.fillStyle=`rgba(0,160,255,${0.4*pulse})`
      ctx.fillText('90°N',6,14); ctx.fillText('90°S',6,H-14); ctx.fillText('180°W',6,H/2); ctx.fillText('180°E',W-36,H/2)
    }
    const id = setInterval(draw, 1000/30); return () => clearInterval(id)
  }, [])
  return <canvas ref={canvasRef} width={820} height={160} style={{display:'block',width:'100%'}}/>
}

/* ─── IRON MAN SUIT ──────────────────────────────────────────── */
const IronManCanvas = ({ active, rotY }) => {
  const canvasRef = useRef(null)
  const rotRef = useRef(rotY); const activeRef = useRef(active)
  useEffect(() => { rotRef.current = rotY }, [rotY])
  useEffect(() => { activeRef.current = active }, [active])
  useEffect(() => {
    const canvas = canvasRef.current; if (!canvas) return
    const ctx = canvas.getContext('2d'); let frame=0, animId
    const W=canvas.width, H=canvas.height, cx=W/2
    const glow=(x,y,r,alpha,color=[0,220,255])=>{const g=ctx.createRadialGradient(x,y,0,x,y,r);g.addColorStop(0,`rgba(${color},${alpha})`);g.addColorStop(0.5,`rgba(${color},${alpha*0.4})`);g.addColorStop(1,'rgba(0,0,0,0)');ctx.fillStyle=g;ctx.beginPath();ctx.arc(x,y,r,0,Math.PI*2);ctx.fill()}
    const seg=(pts,gA=0.7,fA=0.08,color='0,220,255',gColor='0,200,255')=>{ctx.beginPath();pts.forEach(([x,y],i)=>i===0?ctx.moveTo(x,y):ctx.lineTo(x,y));ctx.closePath();ctx.fillStyle=`rgba(${color},${fA})`;ctx.fill();ctx.shadowColor=`rgba(${gColor},0.8)`;ctx.shadowBlur=8;ctx.strokeStyle=`rgba(${color},${gA})`;ctx.lineWidth=1.2;ctx.stroke();ctx.shadowBlur=0}
    const draw=()=>{
      frame++;ctx.clearRect(0,0,W,H)
      const rot=rotRef.current,speak=activeRef.current
      const skew=Math.sin((rot*Math.PI)/180)*0.08,sx=Math.abs(Math.cos((rot*Math.PI)/180))*0.18+0.82
      const pulse=Math.sin(frame*0.04)*0.2+0.8,breathe=Math.sin(frame*0.025)*0.05+0.95,arcPulse=speak?pulse:0.7
      ctx.save();ctx.translate(cx,8);ctx.transform(sx,0,skew,1,0,0);ctx.translate(-cx,0)
      const bg=ctx.createRadialGradient(cx,H*0.42,10,cx,H*0.42,W*0.55);bg.addColorStop(0,`rgba(0,180,255,${0.06*breathe})`);bg.addColorStop(0.5,`rgba(0,160,255,${0.03*breathe})`);bg.addColorStop(1,'rgba(0,0,0,0)');ctx.fillStyle=bg;ctx.fillRect(0,0,W,H)
      const S=(pts,bA=0.8,fA=0.1,c='160,230,255')=>seg(pts,bA*breathe,fA*breathe,c)
      const ln=(x1,y1,x2,y2,a=0.3,w=0.6)=>{ctx.beginPath();ctx.moveTo(x1,y1);ctx.lineTo(x2,y2);ctx.strokeStyle=`rgba(160,230,255,${a})`;ctx.lineWidth=w;ctx.stroke()}
      S([[cx-20,10],[cx-24,18],[cx-26,30],[cx-24,44],[cx-18,52],[cx,54],[cx+18,52],[cx+24,44],[cx+26,30],[cx+24,18],[cx+20,10],[cx+12,7],[cx,5],[cx-12,7]],0.85,0.12,'180,240,255')
      S([[cx-24,20],[cx-28,28],[cx-26,40],[cx-20,44],[cx-18,36],[cx-20,26]],0.6,0.08,'140,220,255')
      S([[cx+24,20],[cx+28,28],[cx+26,40],[cx+20,44],[cx+18,36],[cx+20,26]],0.6,0.08,'140,220,255')
      S([[cx-14,7],[cx-18,14],[cx-16,20],[cx,18],[cx+16,20],[cx+18,14],[cx+14,7],[cx,5]],0.7,0.1,'160,235,255')
      S([[cx-10,44],[cx-8,50],[cx,52],[cx+8,50],[cx+10,44],[cx,46]],0.6,0.07,'140,220,255')
      ln(cx-26,30,cx+26,30,0.4,0.7);ln(cx-26,38,cx+26,38,0.3,0.5);ln(cx,7,cx,54,0.25,0.5)
      const eyeP=speak?pulse:0.88
      ctx.shadowColor='rgba(150,240,255,0.95)';ctx.shadowBlur=speak?20:14
      ctx.beginPath();ctx.moveTo(cx-22,35);ctx.lineTo(cx-16,32);ctx.lineTo(cx-10,34);ctx.lineTo(cx-12,39);ctx.lineTo(cx-18,41);ctx.closePath();ctx.fillStyle=`rgba(200,248,255,${eyeP})`;ctx.fill()
      ctx.beginPath();ctx.moveTo(cx+22,35);ctx.lineTo(cx+16,32);ctx.lineTo(cx+10,34);ctx.lineTo(cx+12,39);ctx.lineTo(cx+18,41);ctx.closePath();ctx.fillStyle=`rgba(200,248,255,${eyeP})`;ctx.fill()
      ctx.shadowBlur=0;glow(cx-16,36,14,eyeP*0.6,'0,210,255');glow(cx+16,36,14,eyeP*0.6,'0,210,255')
      S([[cx-9,54],[cx-9,64],[cx+9,64],[cx+9,54]],0.6,0.08,'140,220,255')
      ln(cx-9,58,cx+9,58,0.3,0.5);ln(cx-9,62,cx+9,62,0.25,0.4)
      S([[cx-40,64],[cx-44,72],[cx-44,90],[cx-42,106],[cx-36,114],[cx,118],[cx+36,114],[cx+42,106],[cx+44,90],[cx+44,72],[cx+40,64],[cx+28,60],[cx,58],[cx-28,60]],0.82,0.13,'170,235,255')
      S([[cx-42,64],[cx-44,78],[cx-36,86],[cx,84],[cx,64],[cx-28,60]],0.55,0.08,'130,215,255')
      S([[cx+42,64],[cx+44,78],[cx+36,86],[cx,84],[cx,64],[cx+28,60]],0.55,0.08,'130,215,255')
      ln(cx,58,cx,118,0.3,0.5);ln(cx-42,72,cx+42,72,0.25,0.5);ln(cx-44,86,cx+44,86,0.2,0.45);ln(cx-42,100,cx+42,100,0.18,0.4);ln(cx-40,110,cx+40,110,0.18,0.4)
      ctx.beginPath();ctx.moveTo(cx-40,64);ctx.quadraticCurveTo(cx,60,cx+40,64);ctx.strokeStyle='rgba(180,240,255,0.5)';ctx.lineWidth=0.8;ctx.stroke()
      const ary=84
      glow(cx,ary,28,arcPulse*0.9,'0,200,255')
      for(let i=0;i<12;i++){const ang=(i/12)*Math.PI*2+frame*0.025,r1=17,r2=22;ctx.beginPath();ctx.moveTo(cx+Math.cos(ang)*r1,ary+Math.sin(ang)*r1);ctx.lineTo(cx+Math.cos(ang)*r2,ary+Math.sin(ang)*r2);ctx.shadowColor='rgba(0,230,255,0.8)';ctx.shadowBlur=4;ctx.strokeStyle=i%3===0?`rgba(200,248,255,${0.9*arcPulse})`:`rgba(0,220,255,${0.4*arcPulse})`;ctx.lineWidth=i%3===0?1.8:0.8;ctx.stroke();ctx.shadowBlur=0}
      ctx.beginPath();ctx.arc(cx,ary,16,0,Math.PI*2);ctx.shadowColor='rgba(0,230,255,0.8)';ctx.shadowBlur=6;ctx.strokeStyle=`rgba(180,240,255,${0.9*arcPulse})`;ctx.lineWidth=1.5;ctx.stroke()
      ctx.beginPath();ctx.arc(cx,ary,11,0,Math.PI*2);ctx.strokeStyle=`rgba(0,255,200,${0.8*arcPulse})`;ctx.lineWidth=1;ctx.stroke()
      ctx.beginPath();ctx.arc(cx,ary,6,0,Math.PI*2);ctx.strokeStyle=`rgba(200,248,255,${arcPulse})`;ctx.lineWidth=0.9;ctx.stroke();ctx.shadowBlur=0
      ctx.shadowColor='rgba(200,248,255,0.95)';ctx.shadowBlur=speak?24:16
      const cg=ctx.createRadialGradient(cx,ary,0,cx,ary,5);cg.addColorStop(0,'rgba(240,252,255,1)');cg.addColorStop(0.6,`rgba(0,230,255,${arcPulse})`);cg.addColorStop(1,'rgba(0,180,255,0)');ctx.fillStyle=cg;ctx.beginPath();ctx.arc(cx,ary,5,0,Math.PI*2);ctx.fill();ctx.shadowBlur=0
      for(let a=0;a<8;a++){const ang=a*Math.PI/4+frame*0.012;ctx.beginPath();ctx.moveTo(cx+Math.cos(ang)*6,ary+Math.sin(ang)*6);ctx.lineTo(cx+Math.cos(ang)*13,ary+Math.sin(ang)*13);ctx.strokeStyle=`rgba(180,240,255,${0.6*arcPulse})`;ctx.lineWidth=0.7;ctx.stroke()}
      S([[cx-40,64],[cx-50,60],[cx-60,64],[cx-64,74],[cx-62,90],[cx-54,98],[cx-44,96],[cx-40,88],[cx-40,72]],0.78,0.11,'160,230,255')
      ln(cx-62,70,cx-54,68,0.3,0.5);ln(cx-64,80,cx-56,78,0.25,0.45);ln(cx-62,88,cx-54,86,0.2,0.4)
      S([[cx+40,64],[cx+50,60],[cx+60,64],[cx+64,74],[cx+62,90],[cx+54,98],[cx+44,96],[cx+40,88],[cx+40,72]],0.78,0.11,'160,230,255')
      ln(cx+62,70,cx+54,68,0.3,0.5);ln(cx+64,80,cx+56,78,0.25,0.45);ln(cx+62,88,cx+54,86,0.2,0.4)
      S([[cx-62,90],[cx-64,100],[cx-64,118],[cx-60,126],[cx-52,128],[cx-46,124],[cx-44,114],[cx-44,96]],0.72,0.09,'150,225,255')
      ln(cx-64,102,cx-46,102,0.25,0.45);ln(cx-64,112,cx-46,112,0.22,0.4);ln(cx-64,122,cx-48,122,0.2,0.4)
      S([[cx+62,90],[cx+64,100],[cx+64,118],[cx+60,126],[cx+52,128],[cx+46,124],[cx+44,114],[cx+44,96]],0.72,0.09,'150,225,255')
      ln(cx+64,102,cx+46,102,0.25,0.45);ln(cx+64,112,cx+46,112,0.22,0.4);ln(cx+64,122,cx+48,122,0.2,0.4)
      S([[cx-64,122],[cx-66,128],[cx-62,136],[cx-54,138],[cx-48,134],[cx-46,126],[cx-50,122],[cx-58,120]],0.82,0.12,'170,235,255')
      S([[cx+64,122],[cx+66,128],[cx+62,136],[cx+54,138],[cx+48,134],[cx+46,126],[cx+50,122],[cx+58,120]],0.82,0.12,'170,235,255')
      S([[cx-62,138],[cx-64,148],[cx-64,166],[cx-60,174],[cx-52,176],[cx-46,172],[cx-44,162],[cx-44,138]],0.70,0.09,'150,225,255')
      ln(cx-64,148,cx-46,148,0.22,0.4);ln(cx-64,158,cx-46,158,0.2,0.4);ln(cx-62,168,cx-48,168,0.2,0.4)
      for(let r=0;r<3;r++)for(let c=0;c<2;c++){ctx.beginPath();ctx.arc(cx-58+c*6,150+r*8,1.4,0,Math.PI*2);ctx.fillStyle='rgba(160,230,255,0.45)';ctx.fill()}
      S([[cx+62,138],[cx+64,148],[cx+64,166],[cx+60,174],[cx+52,176],[cx+46,172],[cx+44,162],[cx+44,138]],0.70,0.09,'150,225,255')
      ln(cx+64,148,cx+46,148,0.22,0.4);ln(cx+64,158,cx+46,158,0.2,0.4);ln(cx+62,168,cx+48,168,0.2,0.4)
      for(let r=0;r<3;r++)for(let c=0;c<2;c++){ctx.beginPath();ctx.arc(cx+52+c*6,150+r*8,1.4,0,Math.PI*2);ctx.fillStyle='rgba(160,230,255,0.45)';ctx.fill()}
      S([[cx-60,176],[cx-62,182],[cx-60,190],[cx-54,194],[cx-46,192],[cx-42,186],[cx-42,176],[cx-52,174]],0.80,0.11,'160,230,255')
      glow(cx-52,192,10,speak?arcPulse*0.9:0.3,'0,200,255')
      ctx.shadowColor=speak?'rgba(0,255,200,0.9)':'rgba(0,200,255,0.4)';ctx.shadowBlur=speak?18:7
      ctx.beginPath();ctx.arc(cx-52,192,7,0,Math.PI*2);ctx.strokeStyle=`rgba(0,255,200,${speak?0.95:0.6})`;ctx.lineWidth=1.3;ctx.stroke()
      ctx.beginPath();ctx.arc(cx-52,192,3.5,0,Math.PI*2);ctx.fillStyle=`rgba(180,255,240,${speak?0.95:0.5})`;ctx.fill();ctx.shadowBlur=0
      S([[cx+60,176],[cx+62,182],[cx+60,190],[cx+54,194],[cx+46,192],[cx+42,186],[cx+42,176],[cx+52,174]],0.80,0.11,'160,230,255')
      glow(cx+52,192,10,speak?arcPulse*0.9:0.3,'0,200,255')
      ctx.shadowColor=speak?'rgba(0,255,200,0.9)':'rgba(0,200,255,0.4)';ctx.shadowBlur=speak?18:7
      ctx.beginPath();ctx.arc(cx+52,192,7,0,Math.PI*2);ctx.strokeStyle=`rgba(0,255,200,${speak?0.95:0.6})`;ctx.lineWidth=1.3;ctx.stroke()
      ctx.beginPath();ctx.arc(cx+52,192,3.5,0,Math.PI*2);ctx.fillStyle=`rgba(180,255,240,${speak?0.95:0.5})`;ctx.fill();ctx.shadowBlur=0
      S([[cx-36,114],[cx-38,122],[cx-38,140],[cx-34,148],[cx,150],[cx+34,148],[cx+38,140],[cx+38,122],[cx+36,114],[cx,118]],0.75,0.10,'150,225,255')
      const tiles=[[cx-26,118],[cx-12,118],[cx+2,118],[cx+16,118],[cx-20,128],[cx-6,128],[cx+8,128],[cx+22,128],[cx-26,138],[cx-12,138],[cx+2,138],[cx+16,138]]
      tiles.forEach(([tx,ty])=>{const hw=6,hh=4;ctx.beginPath();ctx.moveTo(tx,ty-hh);ctx.lineTo(tx+hw,ty-hh/2);ctx.lineTo(tx+hw,ty+hh/2);ctx.lineTo(tx,ty+hh);ctx.lineTo(tx-hw,ty+hh/2);ctx.lineTo(tx-hw,ty-hh/2);ctx.closePath();ctx.strokeStyle='rgba(160,230,255,0.25)';ctx.lineWidth=0.4;ctx.stroke()})
      ln(cx,118,cx,150,0.28,0.5)
      S([[cx-34,148],[cx-36,154],[cx-34,160],[cx,162],[cx+34,160],[cx+36,154],[cx+34,148],[cx,150]],0.72,0.09,'150,225,255')
      S([[cx-36,154],[cx-40,158],[cx-40,166],[cx-32,170],[cx-24,168],[cx-22,160],[cx-26,154]],0.6,0.08,'130,215,255')
      S([[cx+36,154],[cx+40,158],[cx+40,166],[cx+32,170],[cx+24,168],[cx+22,160],[cx+26,154]],0.6,0.08,'130,215,255')
      S([[cx-34,168],[cx-36,178],[cx-36,200],[cx-32,216],[cx-24,220],[cx-16,218],[cx-12,208],[cx-12,188],[cx-16,174],[cx-24,168]],0.72,0.10,'150,225,255')
      ln(cx-36,182,cx-14,180,0.22,0.4);ln(cx-36,194,cx-14,192,0.2,0.4);ln(cx-36,206,cx-14,204,0.2,0.4)
      for(let r=0;r<4;r++){ctx.beginPath();ctx.arc(cx-22,180+r*10,1.5,0,Math.PI*2);ctx.fillStyle='rgba(160,230,255,0.4)';ctx.fill()}
      S([[cx+34,168],[cx+36,178],[cx+36,200],[cx+32,216],[cx+24,220],[cx+16,218],[cx+12,208],[cx+12,188],[cx+16,174],[cx+24,168]],0.72,0.10,'150,225,255')
      ln(cx+36,182,cx+14,180,0.22,0.4);ln(cx+36,194,cx+14,192,0.2,0.4);ln(cx+36,206,cx+14,204,0.2,0.4)
      for(let r=0;r<4;r++){ctx.beginPath();ctx.arc(cx+22,180+r*10,1.5,0,Math.PI*2);ctx.fillStyle='rgba(160,230,255,0.4)';ctx.fill()}
      S([[cx-36,216],[cx-38,224],[cx-34,234],[cx-26,238],[cx-16,236],[cx-12,228],[cx-12,218],[cx-16,214],[cx-26,214]],0.82,0.12,'170,235,255')
      ctx.beginPath();ctx.arc(cx-24,228,7,0,Math.PI*2);ctx.strokeStyle='rgba(180,240,255,0.5)';ctx.lineWidth=0.8;ctx.stroke()
      S([[cx+36,216],[cx+38,224],[cx+34,234],[cx+26,238],[cx+16,236],[cx+12,228],[cx+12,218],[cx+16,214],[cx+26,214]],0.82,0.12,'170,235,255')
      ctx.beginPath();ctx.arc(cx+24,228,7,0,Math.PI*2);ctx.strokeStyle='rgba(180,240,255,0.5)';ctx.lineWidth=0.8;ctx.stroke()
      S([[cx-34,238],[cx-36,248],[cx-36,270],[cx-32,284],[cx-24,288],[cx-16,286],[cx-12,274],[cx-12,252],[cx-12,238]],0.70,0.09,'150,225,255')
      ln(cx-34,248,cx-14,246,0.22,0.4);ln(cx-36,260,cx-14,258,0.2,0.4);ln(cx-36,272,cx-14,270,0.2,0.4)
      S([[cx+34,238],[cx+36,248],[cx+36,270],[cx+32,284],[cx+24,288],[cx+16,286],[cx+12,274],[cx+12,252],[cx+12,238]],0.70,0.09,'150,225,255')
      ln(cx+34,248,cx+14,246,0.22,0.4);ln(cx+36,260,cx+14,258,0.2,0.4);ln(cx+36,272,cx+14,270,0.2,0.4)
      S([[cx-34,286],[cx-36,294],[cx-34,302],[cx-26,308],[cx-16,308],[cx-10,302],[cx-10,290],[cx-12,284]],0.78,0.11,'160,230,255')
      ctx.shadowColor=speak?'rgba(0,255,200,0.8)':'rgba(0,200,255,0.3)';ctx.shadowBlur=speak?16:5
      ctx.beginPath();ctx.ellipse(cx-23,306,11,4,0,0,Math.PI*2);ctx.strokeStyle=`rgba(0,255,200,${speak?0.9:0.5})`;ctx.lineWidth=1;ctx.stroke()
      ctx.beginPath();ctx.ellipse(cx-23,306,6,2,0,0,Math.PI*2);ctx.fillStyle=`rgba(180,255,240,${speak?0.7:0.25})`;ctx.fill();ctx.shadowBlur=0
      S([[cx+34,286],[cx+36,294],[cx+34,302],[cx+26,308],[cx+16,308],[cx+10,302],[cx+10,290],[cx+12,284]],0.78,0.11,'160,230,255')
      ctx.shadowColor=speak?'rgba(0,255,200,0.8)':'rgba(0,200,255,0.3)';ctx.shadowBlur=speak?16:5
      ctx.beginPath();ctx.ellipse(cx+23,306,11,4,0,0,Math.PI*2);ctx.strokeStyle=`rgba(0,255,200,${speak?0.9:0.5})`;ctx.lineWidth=1;ctx.stroke()
      ctx.beginPath();ctx.ellipse(cx+23,306,6,2,0,0,Math.PI*2);ctx.fillStyle=`rgba(180,255,240,${speak?0.7:0.25})`;ctx.fill();ctx.shadowBlur=0
      const baseg=ctx.createRadialGradient(cx,314,0,cx,314,60);baseg.addColorStop(0,`rgba(0,200,255,${0.4*pulse})`);baseg.addColorStop(1,'rgba(0,0,0,0)');ctx.fillStyle=baseg;ctx.beginPath();ctx.ellipse(cx,314,60,14,0,0,Math.PI*2);ctx.fill()
      ctx.restore()
      animId=requestAnimationFrame(draw)
    }
    animId=requestAnimationFrame(draw)
    return ()=>cancelAnimationFrame(animId)
  },[])
  return <canvas ref={canvasRef} width={260} height={310} style={{display:'block'}}/>
}

/* ─── CAIRO HOLOGRAM ─────────────────────────────────────────── */
const CairoHologram = () => {
  const canvasRef = useRef(null)
  useEffect(() => {
    const canvas = canvasRef.current; if (!canvas) return
    const ctx = canvas.getContext('2d'); let frame=0
    const buildings = [
      {x:10,w:30,h:60,type:'pyramid'},{x:50,w:20,h:90,type:'tower'},{x:78,w:35,h:50,type:'pyramid'},
      {x:120,w:15,h:110,type:'minaret'},{x:142,w:28,h:70,type:'tower'},{x:178,w:12,h:95,type:'minaret'},
      {x:198,w:40,h:55,type:'pyramid'},{x:246,w:18,h:85,type:'tower'},{x:272,w:25,h:65,type:'tower'},
      {x:305,w:14,h:100,type:'minaret'},{x:328,w:32,h:58,type:'pyramid'},{x:368,w:16,h:88,type:'tower'},
      {x:392,w:22,h:72,type:'tower'},{x:422,w:10,h:105,type:'minaret'},{x:440,w:36,h:48,type:'pyramid'},{x:484,w:20,h:80,type:'tower'},
    ]
    const draw=()=>{
      ctx.clearRect(0,0,canvas.width,canvas.height);frame++
      const baseY=canvas.height-20,pulse=Math.sin(frame*0.03)*0.25+0.75,pulse2=Math.sin(frame*0.05+1)*0.18+0.82
      ctx.strokeStyle='rgba(0,212,255,0.12)';ctx.lineWidth=0.5
      for(let x=0;x<canvas.width;x+=20){ctx.beginPath();ctx.moveTo(x,baseY);ctx.lineTo(canvas.width/2+(x-canvas.width/2)*0.28,baseY-20);ctx.stroke()}
      for(let i=0;i<6;i++){const y=baseY-i*4;ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(canvas.width,y);ctx.stroke()}
      buildings.forEach((b,idx)=>{
        const bP=Math.sin(frame*0.04+idx*0.5)*0.15+0.85,top=baseY-b.h
        if(b.type==='pyramid'){ctx.shadowColor='rgba(0,212,255,0.6)';ctx.shadowBlur=4;ctx.beginPath();ctx.moveTo(b.x+b.w/2,top);ctx.lineTo(b.x+b.w,baseY);ctx.lineTo(b.x,baseY);ctx.closePath();ctx.strokeStyle=`rgba(0,212,255,${0.85*bP})`;ctx.lineWidth=1.2;ctx.stroke();ctx.fillStyle='rgba(0,200,255,0.07)';ctx.fill();ctx.shadowBlur=0}
        else if(b.type==='minaret'){ctx.shadowColor='rgba(0,212,255,0.5)';ctx.shadowBlur=3;ctx.strokeStyle=`rgba(0,212,255,${0.80*bP})`;ctx.lineWidth=1.1;ctx.strokeRect(b.x+b.w*0.3,top+b.h*0.3,b.w*0.4,b.h*0.7);ctx.beginPath();ctx.arc(b.x+b.w/2,top+b.h*0.3,b.w*0.35,Math.PI,0);ctx.stroke();ctx.beginPath();ctx.moveTo(b.x+b.w/2,top);ctx.lineTo(b.x+b.w/2,top+b.h*0.1);ctx.strokeStyle=`rgba(0,255,200,${0.95*bP})`;ctx.lineWidth=1.8;ctx.stroke();ctx.shadowBlur=0;ctx.strokeStyle=`rgba(0,212,255,${0.65*bP})`;ctx.lineWidth=1;ctx.strokeRect(b.x,baseY-b.h*0.12,b.w,b.h*0.12)}
        else{ctx.shadowColor='rgba(0,212,255,0.4)';ctx.shadowBlur=3;ctx.strokeStyle=`rgba(0,212,255,${0.80*bP})`;ctx.lineWidth=1.1;ctx.strokeRect(b.x,top,b.w,b.h);ctx.fillStyle='rgba(0,212,255,0.05)';ctx.fillRect(b.x,top,b.w,b.h);ctx.shadowBlur=0;const cols=Math.max(2,Math.floor(b.w/6)),rows=Math.max(3,Math.floor(b.h/10));for(let r=0;r<rows;r++)for(let c=0;c<cols;c++){if(Math.sin(frame*0.02+idx*1.3+r*0.7+c*1.1)>0.35){ctx.fillStyle=`rgba(0,255,180,${0.45*bP})`;ctx.fillRect(b.x+2+c*(b.w-4)/cols,top+4+r*(b.h-8)/rows,(b.w-4)/cols-1,(b.h-8)/rows-2)}};if(b.h>75){ctx.beginPath();ctx.moveTo(b.x+b.w/2,top);ctx.lineTo(b.x+b.w/2,top-12);ctx.strokeStyle=`rgba(0,255,200,${0.95*bP})`;ctx.lineWidth=1.4;ctx.stroke();ctx.shadowColor='rgba(255,60,60,0.8)';ctx.shadowBlur=6;ctx.beginPath();ctx.arc(b.x+b.w/2,top-12,2.2,0,Math.PI*2);ctx.fillStyle=`rgba(255,60,60,${bP})`;ctx.fill();ctx.shadowBlur=0}}
      })
      const scanX=((frame*2)%(canvas.width+40))-20;const sg=ctx.createLinearGradient(scanX-15,0,scanX+15,0);sg.addColorStop(0,'rgba(0,212,255,0)');sg.addColorStop(0.5,'rgba(0,212,255,0.28)');sg.addColorStop(1,'rgba(0,212,255,0)');ctx.fillStyle=sg;ctx.fillRect(scanX-15,0,30,canvas.height)
      const gg=ctx.createLinearGradient(0,baseY,canvas.width,baseY);gg.addColorStop(0,'rgba(0,212,255,0)');gg.addColorStop(0.3,`rgba(0,212,255,${0.65*pulse2})`);gg.addColorStop(0.7,`rgba(0,212,255,${0.65*pulse2})`);gg.addColorStop(1,'rgba(0,212,255,0)');ctx.shadowColor='rgba(0,212,255,0.6)';ctx.shadowBlur=6;ctx.strokeStyle=gg;ctx.lineWidth=1.8;ctx.beginPath();ctx.moveTo(0,baseY);ctx.lineTo(canvas.width,baseY);ctx.stroke();ctx.shadowBlur=0
      ctx.font='9px "Share Tech Mono",monospace';ctx.fillStyle=`rgba(0,212,255,${0.65*pulse})`;ctx.fillText('◈ CAIRO, EG  —  30.0444° N  31.2357° E',10,canvas.height-4)
    }
    const id=setInterval(draw,1000/30);return()=>clearInterval(id)
  },[])
  return <canvas ref={canvasRef} width={520} height={168} style={{display:'block'}}/>
}

/* ─── ALERT TICKER ───────────────────────────────────────────── */
const AlertTicker = ({ visible }) => {
  const items = [
    '◈ ALL SYSTEMS NOMINAL','⬡ POWER CORE: 100%','◈ PERIMETER: SECURE','⬡ UPLINK: ESTABLISHED',
    '◈ AI CORE: ONLINE','⬡ THREAT LEVEL: MINIMAL','◈ MEMORY BANKS: ACTIVE','⬡ ENCRYPTION: AES-256',
    '◈ NETWORK: SECURE','⬡ FIRMWARE: CURRENT','◈ BIOMETRICS: VERIFIED','⬡ AGENT17-TECH AUTH OK',
    '◈ HINDSIGHT: CONNECTED','⬡ VAULT: ENCRYPTED','◈ SANDBOX: ENFORCED','⬡ SENSORS: 4 ACTIVE',
    '◈ SCHEDULER: 9 TRIGGERS','⬡ AGENTS: 6 ONLINE','◈ MKIII: PHASE 4 COMPLETE',
  ]
  const text = items.join('   //   ')+'   //   '+items.join('   //   ')
  return (
    <div style={{position:'fixed',bottom:0,left:0,right:0,height:24,zIndex:50,background:'rgba(0,4,14,0.97)',borderTop:'1px solid rgba(0,212,255,0.18)',overflow:'hidden',opacity:visible?1:0,transition:'opacity 1s ease',display:'flex',alignItems:'center'}}>
      <div style={{flexShrink:0,height:'100%',background:'rgba(0,212,255,0.07)',borderRight:'1px solid rgba(0,212,255,0.18)',display:'flex',alignItems:'center',padding:'0 14px',fontFamily:'Orbitron',fontSize:8,fontWeight:700,color:'rgba(0,212,255,0.92)',letterSpacing:2.5,whiteSpace:'nowrap'}}>SYS FEED</div>
      <div style={{overflow:'hidden',flex:1,height:'100%',display:'flex',alignItems:'center'}}>
        <div style={{display:'inline-block',whiteSpace:'nowrap',fontFamily:'Share Tech Mono',fontSize:9,color:'rgba(0,185,255,0.68)',letterSpacing:1.5,animation:'tickerScroll 42s linear infinite'}}>{text}</div>
      </div>
      <div style={{flexShrink:0,height:'100%',borderLeft:'1px solid rgba(0,212,255,0.18)',display:'flex',alignItems:'center',padding:'0 14px',gap:6}}>
        <div style={{width:5,height:5,borderRadius:'50%',background:'#00ffc8',boxShadow:'0 0 7px #00ffc8',animation:'blink 2s ease-in-out infinite'}}/>
        <span style={{fontFamily:'Share Tech Mono',fontSize:8,color:'#00ffc8',letterSpacing:1.5}}>LIVE</span>
      </div>
    </div>
  )
}

/* ─── STAT BAR ───────────────────────────────────────────────── */
const StatBar = ({ label, value, max=100, color, unit='%' }) => (
  <div style={{marginBottom:10}}>
    <div style={S.statRow}>
      <span style={S.dimText}>{label}</span>
      <span style={{color,fontFamily:'Share Tech Mono',fontSize:12,textShadow:`0 0 8px ${color}`}}>{value}{unit}</span>
    </div>
    <div style={S.barBg}>
      <div style={{...S.barFill,width:`${(value/max)*100}%`,background:`linear-gradient(90deg,${color}88,${color})`,boxShadow:`0 0 8px ${color}`,transition:'width 1.2s cubic-bezier(0.4,0,0.2,1)'}}/>
    </div>
  </div>
)

/* ─── CORNER BRACKETS ────────────────────────────────────────── */
const Corner = ({ pos }) => {
  const sz=50,th=2,c='rgba(0,212,255,0.65)'
  const p={topLeft:{top:14,left:14,borderTop:`${th}px solid ${c}`,borderLeft:`${th}px solid ${c}`},topRight:{top:14,right:14,borderTop:`${th}px solid ${c}`,borderRight:`${th}px solid ${c}`},bottomLeft:{bottom:30,left:14,borderBottom:`${th}px solid ${c}`,borderLeft:`${th}px solid ${c}`},bottomRight:{bottom:30,right:14,borderBottom:`${th}px solid ${c}`,borderRight:`${th}px solid ${c}`}}
  return <div style={{position:'fixed',width:sz,height:sz,animation:'cornerPulse 3s ease-in-out infinite',...p[pos]}}/>
}

/* ─── STYLE SHEET ────────────────────────────────────────────── */
const S = {
  root:{width:'100vw',height:'100vh',background:'rgba(0,6,16,0.97)',position:'relative',overflow:'hidden'},
  grid:{position:'fixed',inset:0,backgroundImage:'linear-gradient(rgba(0,160,255,0.028) 1px,transparent 1px),linear-gradient(90deg,rgba(0,160,255,0.028) 1px,transparent 1px)',backgroundSize:'44px 44px',pointerEvents:'none'},
  scanlines:{position:'fixed',inset:0,background:'repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,0,0,0.052) 2px,rgba(0,0,0,0.052) 4px)',pointerEvents:'none'},
  vignette:{position:'fixed',inset:0,background:'radial-gradient(ellipse at center,transparent 55%,rgba(0,0,0,0.6) 100%)',pointerEvents:'none'},
  bootScanline:{position:'fixed',left:0,right:0,height:4,background:'linear-gradient(90deg,transparent,#00d4ff,transparent)',boxShadow:'0 0 24px #00d4ff,0 0 48px rgba(0,212,255,0.4)',animation:'bootScan 0.9s ease-in forwards',zIndex:100},
  panel:{position:'fixed',background:'rgba(0,7,22,0.88)',border:'1px solid rgba(0,212,255,0.2)',borderRadius:3,padding:'14px 18px',width:274,backdropFilter:'blur(6px)',boxShadow:'0 0 22px rgba(0,80,180,0.08),inset 0 1px 0 rgba(0,212,255,0.07)'},
  topLeft:{top:50,left:36},
  topRight:{top:158,right:36},
  panelTitle:{fontFamily:'Orbitron',fontSize:9,fontWeight:700,letterSpacing:3.5,color:'rgba(0,200,255,0.9)',marginBottom:13,textShadow:'0 0 12px rgba(0,200,255,0.35)'},
  statRow:{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:5},
  dimText:{fontFamily:'Share Tech Mono',fontSize:10,color:'rgba(0,140,200,0.52)',letterSpacing:1.2},
  valueText:{fontFamily:'Share Tech Mono',fontSize:11,color:'rgba(0,212,255,0.92)',textShadow:'0 0 8px rgba(0,212,255,0.3)'},
  barBg:{width:'100%',height:2.5,background:'rgba(0,120,220,0.12)',borderRadius:2,overflow:'hidden'},
  barFill:{height:'100%',borderRadius:2},
  divider:{width:'100%',height:1,background:'linear-gradient(90deg,transparent,rgba(0,212,255,0.2),transparent)',margin:'11px 0'},
  clock:{fontFamily:'Orbitron',fontSize:30,fontWeight:700,color:'rgba(0,220,255,0.97)',textShadow:'0 0 24px rgba(0,212,255,0.5)',letterSpacing:4,marginBottom:5},
  date:{fontFamily:'Share Tech Mono',fontSize:9,color:'rgba(0,140,200,0.52)',letterSpacing:1},
  logList:{display:'flex',flexDirection:'column',gap:8},
  logItem:{display:'flex',alignItems:'center',gap:10},
  logDot:{width:5,height:5,borderRadius:'50%',flexShrink:0},
  logText:{fontFamily:'Share Tech Mono',fontSize:10,color:'rgba(150,210,255,0.82)',letterSpacing:0.5},
  chatLog:{display:'flex',flexDirection:'column',gap:10,minHeight:100,maxHeight:170,overflowY:'auto',scrollbarWidth:'none'},
  chatMessage:{display:'flex',gap:8,alignItems:'flex-start'},
  chatLabel:{fontFamily:'Orbitron',fontSize:9,flexShrink:0,marginTop:2,letterSpacing:1},
  chatText:{fontFamily:'Share Tech Mono',fontSize:11,color:'rgba(160,215,255,0.88)',lineHeight:1.7},
  cursor:{animation:'blink 0.7s step-end infinite',color:'#00d4ff'},
  inputRow:{display:'flex',alignItems:'center',gap:8},
  input:{background:'transparent',border:'none',outline:'none',color:'rgba(0,212,255,0.92)',fontFamily:'Share Tech Mono',fontSize:11,width:'100%',letterSpacing:1,caretColor:'#00d4ff'},
  center:{position:'fixed',top:'50%',left:'50%',transform:'translate(-50%,-50%)',display:'flex',flexDirection:'column',alignItems:'center',gap:10},
  arcOuter:{position:'relative',width:410,height:410,display:'flex',alignItems:'center',justifyContent:'center'},
  arcLabel:{fontFamily:'Orbitron',fontSize:14,fontWeight:900,letterSpacing:9,color:'rgba(0,212,255,0.96)',textShadow:'0 0 24px rgba(0,212,255,0.7)'},
  arcSub:{fontFamily:'Share Tech Mono',fontSize:9,letterSpacing:5,color:'rgba(0,140,200,0.48)'},
}

/* ─── HUD ────────────────────────────────────────────────────── */
const HUD = () => {
  const [stats,setStats]           = useState({cpu:0,ram:0,temp:0})
  const [time,setTime]             = useState(new Date())
  const [messages,setMessages]     = useState([])
  const [input,setInput]           = useState('')
  const [isThinking,setIsThinking] = useState(false)
  const [isSpeaking,setIsSpeaking] = useState(false)
  const [isListening,setIsListening] = useState(false)
  const [boot,setBoot]             = useState({})
  const [booted,setBooted]         = useState(false)
  const [shutting,setShutting]     = useState(false)
  const [shutStep,setShutStep]     = useState(0)
  const [rotY,setRotY]             = useState(0)
  const [weather,setWeather]       = useState(null)
  const [repos,setRepos]           = useState([])
  const [activeRepo,setActiveRepo] = useState(null)
  const chatEndRef     = useRef(null)
  const hasGreeted     = useRef(false)
  const wsRef          = useRef(null)
  const pendingVoiceId = useRef(null)

  useEffect(()=>{const id=setInterval(()=>setRotY(p=>(p+0.35)%360),16);return()=>clearInterval(id)},[])

  useEffect(()=>{
    BOOT_STEPS.forEach(({key,delay})=>{
      setTimeout(()=>{
        setBoot(prev=>({...prev,[key]:true}))
        if(key==='ready'){
          setBooted(true)
          if(wsRef.current)wsRef.current.close()
          const ws=new WebSocket('ws://localhost:8000/ws')
          wsRef.current=ws
          ws.onmessage=(e)=>{
            if(e.data==='speaking:start')setIsSpeaking(true)
            if(e.data==='speaking:stop')setIsSpeaking(false)
            if(e.data==='shutdown:start')triggerShutdown()
            if(e.data==='voice:listening')setIsListening(true)
            if(e.data==='voice:processing')setIsListening(false)
            if(e.data.startsWith('voice:transcript:')){
              const text=e.data.replace('voice:transcript:','')
              const uid=Date.now(),jid=uid+1
              pendingVoiceId.current=jid
              setMessages(prev=>[...prev,{id:uid,text,type:'user'},{id:jid,text:'...',type:'jarvis'}])
              setIsThinking(true)
            }
            if(e.data.startsWith('voice:response:')){
              const text=e.data.replace('voice:response:','')
              const jid=pendingVoiceId.current
              if(jid){setMessages(prev=>prev.map(m=>m.id===jid?{...m,text}:m))}
              else{setMessages(prev=>[...prev,{id:Date.now(),text,type:'jarvis'}])}
              setIsThinking(false);pendingVoiceId.current=null
            }
          }
          fetch('http://localhost:8000/greeting').then(r=>r.json()).then(data=>{
            setMessages([{id:1,text:data.greeting,type:'jarvis'}])
            if(!hasGreeted.current){hasGreeted.current=true;fetch('http://localhost:8000/speak',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:data.greeting})}).catch(()=>{})}
          }).catch(()=>setMessages([{id:1,text:'All systems online, sir.',type:'jarvis'}]))
        }
      },delay)
    })
  },[])

  useEffect(()=>{if(window.jarvis)window.jarvis.onSystemStats(d=>setStats(d))},[])
  useEffect(()=>{const t=setInterval(()=>setTime(new Date()),1000);return()=>clearInterval(t)},[])
  useEffect(()=>{const fw=()=>fetch('http://localhost:8000/weather').then(r=>r.json()).then(d=>{if(!d.error)setWeather(d)}).catch(()=>{});fw();const id=setInterval(fw,600000);return()=>clearInterval(id)},[])
  useEffect(()=>{const fg=()=>fetch('http://localhost:8000/github').then(r=>r.json()).then(d=>{if(Array.isArray(d))setRepos(d)}).catch(()=>{});fg();const id=setInterval(fg,5*60*1000);return()=>clearInterval(id)},[])
  useEffect(()=>{chatEndRef.current?.scrollIntoView({behavior:'smooth'})},[messages])

  const formatTime=d=>d.toLocaleTimeString('en-US',{hour12:false})
  const formatDate=d=>d.toLocaleDateString('en-US',{weekday:'long',year:'numeric',month:'long',day:'numeric'})

  const triggerShutdown=async()=>{
    if(shutting)return;setShutting(true)
    fetch('http://localhost:8000/shutdown',{method:'POST'}).catch(()=>{})
    setTimeout(()=>setShutStep(1),50);setTimeout(()=>setShutStep(2),400)
    setTimeout(()=>setShutStep(3),700);setTimeout(()=>setShutStep(4),1000)
    setTimeout(()=>setShutStep(5),1300);setTimeout(()=>setShutStep(6),1800)
    setTimeout(()=>setShutStep(7),2200)
    setTimeout(()=>{if(window.require){const{remote}=window.require('@electron/remote');if(remote)remote.getCurrentWindow().close()}},2800)
  }

  const sendMessage=async()=>{
    if(!input.trim()||isThinking)return
    const lower=input.trim().toLowerCase()
    if(['shutdown','power down','jarvis shutdown','offline'].includes(lower)){setInput('');triggerShutdown();return}
    const userMsg={id:Date.now(),text:input,type:'user'}
    setMessages(prev=>[...prev,userMsg]);setInput('');setIsThinking(true)
    const jid=Date.now()+1;setMessages(prev=>[...prev,{id:jid,text:'',type:'jarvis'}])
    try{
      const res=await fetch('http://localhost:8000/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({content:input})})
      const reader=res.body.getReader(),dec=new TextDecoder()
      while(true){const{done,value}=await reader.read();if(done)break;const tok=dec.decode(value);setMessages(prev=>prev.map(m=>m.id===jid?{...m,text:m.text+tok}:m))}
    }catch{setMessages(prev=>prev.map(m=>m.id===jid?{...m,text:'Connection to backend lost, sir.'}:m))}
    finally{setIsThinking(false)}
  }
  const handleKey=e=>{if(e.key==='Enter')sendMessage()}

  const scanScreen=async()=>{
    if(isThinking)return
    const userMsg={id:Date.now(),text:'What do you see on my screen?',type:'user'}
    setMessages(prev=>[...prev,userMsg]);setIsThinking(true)
    const jid=Date.now()+1;setMessages(prev=>[...prev,{id:jid,text:'',type:'jarvis'}])
    try{
      const res=await fetch('http://localhost:8000/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({content:'What do you see on my screen right now?'})})
      const reader=res.body.getReader(),dec=new TextDecoder()
      while(true){const{done,value}=await reader.read();if(done)break;const tok=dec.decode(value);setMessages(prev=>prev.map(m=>m.id===jid?{...m,text:m.text+tok}:m))}
    }catch{setMessages(prev=>prev.map(m=>m.id===jid?{...m,text:'Vision scan failed, sir.'}:m))}
    finally{setIsThinking(false)}
  }

  const rb={position:'absolute',borderRadius:'50%'}
  const rings=[
    {...rb,width:410,height:410,border:`1.5px solid rgba(0,180,255,${isSpeaking?0.88:0.36})`,borderTopColor:`rgba(0,230,255,${isSpeaking?1:0.9})`,boxShadow:isSpeaking?'0 0 45px rgba(0,212,255,0.65),0 0 90px rgba(0,180,255,0.3)':'0 0 20px rgba(0,180,255,0.22)',animationName:'spin1',animationTimingFunction:'linear',animationIterationCount:'infinite',animationDuration:isThinking?'0.9s':isSpeaking?'0.45s':'4.2s',transform:isSpeaking?'scale(1.06)':'scale(1)',transition:'transform 0.4s ease,box-shadow 0.4s ease,border-color 0.4s ease'},
    {...rb,width:332,height:332,border:'1px solid rgba(0,155,255,0.2)',borderBottomColor:`rgba(0,212,255,${isSpeaking?0.88:0.55})`,animationName:'spin2',animationTimingFunction:'linear',animationIterationCount:'infinite',animationDuration:isThinking?'0.7s':isSpeaking?'0.35s':'3.1s',transform:isSpeaking?'scale(1.05)':'scale(1)',transition:'transform 0.4s ease'},
    {...rb,width:256,height:256,border:'1px solid rgba(0,155,255,0.26)',borderLeftColor:`rgba(0,200,255,${isSpeaking?0.82:0.6})`,borderRightColor:`rgba(0,200,255,${isSpeaking?0.82:0.6})`,animationName:'spin1',animationTimingFunction:'linear',animationIterationCount:'infinite',animationDuration:isThinking?'1.2s':isSpeaking?'0.6s':'6s',transform:isSpeaking?'scale(1.04)':'scale(1)',transition:'transform 0.4s ease'},
    {...rb,width:182,height:182,border:'1px solid rgba(0,155,255,0.16)',borderTopColor:`rgba(0,255,200,${isSpeaking?0.72:0.44})`,animationName:'spin2',animationTimingFunction:'linear',animationIterationCount:'infinite',animationDuration:isThinking?'1.8s':isSpeaking?'0.8s':'8s'},
    {...rb,width:122,height:122,border:`1px solid rgba(0,255,200,${isSpeaking?0.55:0.2})`,borderBottomColor:`rgba(0,255,200,${isSpeaking?0.92:0.48})`,animationName:'spin1',animationTimingFunction:'linear',animationIterationCount:'infinite',animationDuration:isThinking?'1s':isSpeaking?'0.5s':'5s',transform:isSpeaking?'scale(1.06)':'scale(1)',transition:'transform 0.4s ease'},
  ]

  const missionItems = [
    {t:'JARVIS MKIII — Phase 4 active', s:'active'},
    {t:'Vault — AES-256 encrypted',      s:'active'},
    {t:'Sandbox — Allowlists enforced',   s:'active'},
    {t:'Hindsight Memory — Connected',    s:'active'},
    {t:'Sensors — 4 of 5 active',        s:'active'},
    {t:'Agent Router — 6 agents online',  s:'active'},
    {t:'World State — 60s updates',       s:'active'},
    {t:'Scheduler — 9 triggers armed',    s:'active'},
  ]

  return (
    <div style={{...S.root,filter:shutStep>=7?'brightness(0)':shutStep>=6?'brightness(0.12)':'none',transition:'filter 0.9s ease'}}>

      {/* ── BACKGROUND LAYERS ── */}
      <div style={S.grid}/><div style={S.scanlines}/><div style={S.vignette}/>

      {/* ── SHUTDOWN OVERLAY ── */}
      {shutStep>=6&&<div style={{position:'fixed',inset:0,zIndex:999,pointerEvents:'none',background:`rgba(0,0,0,${shutStep>=7?1:0.65})`,transition:'background 0.7s ease'}}/>}

      {/* ── POWER BUTTON ── */}
      {booted&&!shutting&&(
        <div onClick={triggerShutdown} title="Shutdown JARVIS"
          style={{position:'fixed',top:14,right:14,width:28,height:28,borderRadius:'50%',border:'1px solid rgba(255,60,60,0.38)',display:'flex',alignItems:'center',justifyContent:'center',cursor:'pointer',zIndex:200,background:'rgba(255,30,30,0.07)',transition:'all 0.25s ease'}}
          onMouseEnter={e=>{e.currentTarget.style.borderColor='rgba(255,60,60,0.95)';e.currentTarget.style.boxShadow='0 0 14px rgba(255,50,50,0.6)';e.currentTarget.style.background='rgba(255,30,30,0.22)'}}
          onMouseLeave={e=>{e.currentTarget.style.borderColor='rgba(255,60,60,0.38)';e.currentTarget.style.boxShadow='none';e.currentTarget.style.background='rgba(255,30,30,0.07)'}}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="rgba(255,80,80,0.9)" strokeWidth="2.5" strokeLinecap="round"><path d="M12 2v6M6.3 5.3A9 9 0 1 0 17.7 5.3"/></svg>
        </div>
      )}

      {/* ── BOOT SCANLINE ── */}
      {boot.scanline&&!boot.reactor&&<div style={S.bootScanline}/>}

      {/* ── CORNER BRACKETS ── */}
      {boot.corners&&['topLeft','topRight','bottomLeft','bottomRight'].map(p=><Corner key={p} pos={p}/>)}

      {/* ── WORLD MAP — top center ── */}
      <div style={{position:'fixed',top:0,left:'50%',transform:'translateX(-50%)',width:820,transition:'opacity 0.9s ease',opacity:shutStep>=3?0:boot.worldmap?1:0,zIndex:10}}>
        <div style={{background:'rgba(0,5,18,0.95)',border:'1px solid rgba(0,212,255,0.2)',borderTop:'none',borderRadius:'0 0 4px 4px',overflow:'hidden',boxShadow:'0 4px 30px rgba(0,80,180,0.1)'}}>
          <div style={{padding:'5px 16px 0',display:'flex',justifyContent:'space-between',alignItems:'center'}}>
            <div style={{...S.panelTitle,marginBottom:4}}>GLOBAL NETWORK — TACTICAL OVERVIEW</div>
            <div style={{fontFamily:'Share Tech Mono',fontSize:9,color:'#00ffc8',letterSpacing:1.5}}>● LIVE</div>
          </div>
          <WorldMap/>
        </div>
      </div>

      {/* ── TOP LEFT — WORLD STATE ── */}
      <div style={{position:'fixed',top:50,left:36,zIndex:15,transition:'transform 0.7s cubic-bezier(0.16,1,0.3,1),opacity 0.7s ease',transform:boot.panelTL?'translateX(0)':'translateX(-130px)',opacity:shutStep>=1?0:boot.panelTL?1:0}}>
        <WorldStatePanel/>
      </div>

      {/* ── TOP RIGHT — AGENT FEED ── */}
      <div style={{position:'fixed',top:50,right:36,zIndex:15,transition:'transform 0.7s cubic-bezier(0.16,1,0.3,1),opacity 0.7s ease',transform:boot.panelTR?'translateX(0)':'translateX(130px)',opacity:shutStep>=2?0:boot.mkiii?1:0}}>
        <AgentFeed/>
      </div>

      {/* ── TOP RIGHT — CHRONOS ── */}
      <div style={{...S.panel,...S.topRight,transition:'transform 0.7s cubic-bezier(0.16,1,0.3,1),opacity 0.7s ease',transform:boot.panelTR?'translateX(0)':'translateX(130px)',opacity:shutStep>=1?0:boot.panelTR?1:0}}>
        <div style={S.panelTitle}>CHRONOS</div>
        <div style={S.clock}>{formatTime(time)}</div>
        <div style={S.date}>{formatDate(time)}</div>
        <div style={S.divider}/>
        <div style={S.statRow}><span style={S.dimText}>TEMP</span><span style={{...S.valueText,color:'#ffb900'}}>{weather?`${weather.temp}°C`:'--'}</span></div>
        <div style={S.statRow}><span style={S.dimText}>CONDITIONS</span><span style={{...S.valueText,fontSize:9,textTransform:'uppercase'}}>{weather?weather.condition:'--'}</span></div>
        <div style={S.statRow}><span style={S.dimText}>WIND</span><span style={S.valueText}>{weather?`${weather.wind} km/h`:'--'}</span></div>
        <div style={S.statRow}><span style={S.dimText}>LOCATION</span><span style={S.valueText}>CAIRO, EG</span></div>
      </div>

      {/* ── LEFT — MARK L SCHEMATIC ── */}
      <div style={{position:'fixed',left:36,top:310,width:282,display:'flex',flexDirection:'column',alignItems:'center',transition:'opacity 0.9s ease,transform 0.9s cubic-bezier(0.16,1,0.3,1)',opacity:shutStep>=3?0:boot.suit?1:0,transform:boot.suit?'translateX(0)':'translateX(-130px)'}}>
        <div style={{width:'100%',background:'rgba(0,5,18,0.95)',border:'1px solid rgba(0,212,255,0.2)',borderBottom:'none',borderRadius:'3px 3px 0 0',padding:'7px 16px'}}>
          <div style={S.panelTitle}>MARK L — SCHEMATIC</div>
        </div>
        <div style={{width:'100%',background:'rgba(0,2,14,0.98)',border:'1px solid rgba(0,212,255,0.2)',borderTop:'none',borderRadius:'0 0 3px 3px',padding:'10px 0 8px',display:'flex',flexDirection:'column',alignItems:'center',overflow:'hidden',position:'relative',boxShadow:'inset 0 -20px 40px rgba(0,80,180,0.12)'}}>
          <div style={{position:'absolute',bottom:18,left:'8%',right:'8%',height:28,background:'radial-gradient(ellipse,rgba(0,160,255,0.28) 0%,transparent 70%)',pointerEvents:'none'}}/>
          <IronManCanvas active={isSpeaking} rotY={rotY}/>
          <div style={{display:'flex',gap:18,marginTop:6,padding:'0 12px'}}>
            {[{l:'POWER',v:'100%',c:'#00ffc8'},{l:'ARMOR',v:'100%',c:'#00d4ff'},{l:'THRUSTERS',v:'READY',c:'#ffb900'}].map((s,i)=>(
              <div key={i} style={{textAlign:'center'}}>
                <div style={{fontFamily:'Share Tech Mono',fontSize:8,color:'rgba(0,120,180,0.52)',letterSpacing:1}}>{s.l}</div>
                <div style={{fontFamily:'Orbitron',fontSize:9,color:s.c,letterSpacing:1,textShadow:`0 0 8px ${s.c}`}}>{s.v}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── LEFT — GITHUB PANEL ── */}
      <div style={{position:'fixed',left:36,top:640,width:282,background:'rgba(0,7,22,0.88)',border:'1px solid rgba(0,212,255,0.2)',borderRadius:3,padding:'14px 18px',backdropFilter:'blur(6px)',boxShadow:'0 0 22px rgba(0,80,180,0.08),inset 0 1px 0 rgba(0,212,255,0.07)',transition:'opacity 0.9s ease,transform 0.9s cubic-bezier(0.16,1,0.3,1)',opacity:shutStep>=2?0:boot.github?1:0,transform:boot.github?'translateX(0)':'translateX(-130px)'}}>
        <div style={S.panelTitle}>GITHUB — AGENT17-TECH</div>
        {repos.length===0?(
          <div style={{...S.dimText,fontSize:9}}>FETCHING REPOSITORIES...</div>
        ):(
          <div style={{display:'flex',flexDirection:'column',gap:10,maxHeight:180,overflowY:'auto',scrollbarWidth:'none'}}>
            {repos.map((r,ri)=>(
              <div key={ri} style={{cursor:'pointer'}} onClick={()=>setActiveRepo(activeRepo===ri?null:ri)}>
                <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:2}}>
                  <span style={{fontFamily:'Share Tech Mono',fontSize:10,color:'rgba(0,212,255,0.92)',letterSpacing:0.5}}>{r.name}</span>
                  <span style={{fontFamily:'Share Tech Mono',fontSize:8,color:'rgba(0,255,200,0.6)',letterSpacing:1}}>{r.language||'—'}</span>
                </div>
                {activeRepo===ri&&(
                  <div style={{marginTop:6,paddingTop:6,borderTop:'1px solid rgba(0,212,255,0.1)'}}>
                    {r.commits&&r.commits.length>0?(
                      <div style={{display:'flex',flexDirection:'column',gap:5}}>
                        {r.commits.map((c,ci)=>(
                          <div key={ci} style={{display:'flex',gap:7,alignItems:'flex-start'}}>
                            <span style={{fontFamily:'Share Tech Mono',fontSize:7.5,color:'rgba(0,255,200,0.45)',marginTop:1,flexShrink:0}}>{c.sha}</span>
                            <div style={{flex:1,minWidth:0}}>
                              <div style={{fontFamily:'Share Tech Mono',fontSize:8,color:'rgba(0,212,255,0.85)',whiteSpace:'nowrap',overflow:'hidden',textOverflow:'ellipsis'}}>{c.message}</div>
                              <div style={{...S.dimText,fontSize:7.5,marginTop:1}}>{c.author} · {c.time}</div>
                            </div>
                          </div>
                        ))}
                      </div>
                    ):(
                      <div style={{...S.dimText,fontSize:8}}>NO RECENT COMMITS</div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ── BOTTOM CENTER — CAIRO HOLOGRAM ── */}
      <div style={{position:'fixed',bottom:24,left:'50%',transform:'translateX(-50%)',width:520,transition:'opacity 1s ease',opacity:shutStep>=4?0:boot.cairo?1:0}}>
        <div style={{background:'rgba(0,5,18,0.93)',border:'1px solid rgba(0,212,255,0.2)',borderBottom:'none',borderRadius:'4px 4px 0 0',padding:'6px 16px',display:'flex',justifyContent:'space-between',alignItems:'center'}}>
          <div style={S.panelTitle}>TACTICAL MAP — CAIRO SECTOR</div>
          <div style={{fontFamily:'Share Tech Mono',fontSize:9,color:'#00ffc8',letterSpacing:1.5}}>● LIVE</div>
        </div>
        <div style={{background:'rgba(0,2,12,0.98)',border:'1px solid rgba(0,212,255,0.2)',borderTop:'none',overflow:'hidden',boxShadow:'0 0 30px rgba(0,80,180,0.08)'}}>
          <CairoHologram/>
        </div>
      </div>

      {/* ── RIGHT — JARVIS INTERFACE ── */}
      <div style={{...S.panel,position:'fixed',bottom:290,right:36,width:354,transition:'transform 0.7s cubic-bezier(0.16,1,0.3,1),opacity 0.7s ease',transform:boot.panelBR?'translateX(0)':'translateX(130px)',opacity:shutStep>=1?0:boot.panelBR?1:0}}>
        <div style={S.panelTitle}>J.A.R.V.I.S INTERFACE</div>
        <div style={S.chatLog}>
          {messages.map(m=>(
            <div key={m.id} style={S.chatMessage}>
              <span style={{...S.chatLabel,color:m.type==='user'?'#ffb900':'#00d4ff',textShadow:m.type==='user'?'0 0 8px rgba(255,185,0,0.5)':'0 0 8px rgba(0,212,255,0.5)'}}>{m.type==='user'?'YOU >':'JARVIS >'}</span>
              <span style={S.chatText}>{m.text}{m.text===''&&isThinking&&<span style={S.cursor}>▋</span>}</span>
            </div>
          ))}
          <div ref={chatEndRef}/>
        </div>
        {isListening&&(
          <div style={{display:'flex',alignItems:'center',gap:6,padding:'5px 0',marginBottom:4}}>
            <div style={{width:6,height:6,borderRadius:'50%',background:'#00ffc8',boxShadow:'0 0 8px #00ffc8',animation:'pulse 0.8s ease-in-out infinite'}}/>
            <span style={{fontFamily:'Share Tech Mono',fontSize:9,color:'#00ffc8',letterSpacing:1.5}}>LISTENING...</span>
          </div>
        )}
        <div style={S.divider}/>
        <div style={S.inputRow}>
          <span style={{...S.dimText,color:'rgba(0,212,255,0.45)'}}>&gt;</span>
          <input style={S.input} value={input} onChange={e=>setInput(e.target.value)} onKeyDown={handleKey} placeholder={isThinking?'JARVIS is responding...':'Enter command, sir...'} disabled={isThinking||!booted}/>
          <button onClick={scanScreen} disabled={isThinking||!booted} title="Scan screen"
            style={{background:'none',border:'1px solid rgba(0,212,255,0.25)',borderRadius:3,color:isThinking?'rgba(0,212,255,0.2)':'rgba(0,212,255,0.6)',fontFamily:'Share Tech Mono',fontSize:9,letterSpacing:1,padding:'4px 7px',cursor:isThinking?'not-allowed':'pointer',flexShrink:0,transition:'all 0.2s ease',textShadow:isThinking?'none':'0 0 6px rgba(0,212,255,0.4)'}}
            onMouseEnter={e=>{if(!isThinking)e.target.style.borderColor='rgba(0,212,255,0.7)'}}
            onMouseLeave={e=>{e.target.style.borderColor='rgba(0,212,255,0.25)'}}>
            👁 SCAN
          </button>
        </div>
      </div>

      {/* ── RIGHT — MISSION LOG ── */}
      <div style={{...S.panel,position:'fixed',bottom:100,right:36,width:354,transition:'transform 0.7s cubic-bezier(0.16,1,0.3,1),opacity 0.7s ease',transform:boot.missionlog?'translateX(0)':'translateX(130px)',opacity:shutStep>=2?0:boot.missionlog?1:0}}>
        <div style={S.panelTitle}>MISSION LOG</div>
        <div style={S.logList}>
          {missionItems.map((task,i)=>(
            <div key={i} style={S.logItem}>
              <div style={{...S.logDot,background:task.s==='active'?'#00ffc8':task.s==='pending'?'#ffb900':'#ff3c3c',boxShadow:`0 0 6px ${task.s==='active'?'#00ffc8':task.s==='pending'?'#ffb900':'#ff3c3c'}`}}/>
              <span style={S.logText}>{task.t}</span>
            </div>
          ))}
        </div>
      </div>

      {/* ── ARC REACTOR — center ── */}
      <div style={{...S.center,transition:'opacity 1.1s ease,transform 1.1s cubic-bezier(0.16,1,0.3,1)',opacity:shutStep>=5?0:boot.reactor?1:0,transform:boot.reactor?'translate(-50%,-50%) scale(1)':'translate(-50%,-50%) scale(0.22)'}}>
        <div style={S.arcOuter}>
          {rings.map((r,i)=><div key={i} style={r}/>)}
          <div style={{position:'absolute',width:96,height:96,borderRadius:'50%',background:isSpeaking?'radial-gradient(circle,rgba(0,220,255,0.62) 0%,rgba(0,180,255,0.16) 60%,transparent 100%)':'radial-gradient(circle,rgba(0,200,255,0.28) 0%,rgba(0,180,255,0.06) 70%,transparent 100%)',transition:'background 0.4s ease',animation:'pulse 2.2s ease-in-out infinite',display:'flex',alignItems:'center',justifyContent:'center'}}>
            <div style={{width:56,height:56,borderRadius:'50%',background:'radial-gradient(circle,rgba(180,248,255,0.95) 0%,rgba(0,210,255,0.6) 40%,transparent 100%)',boxShadow:isSpeaking?'0 0 55px #00d4ff,0 0 110px rgba(0,200,255,0.7),0 0 180px rgba(0,180,255,0.3)':'0 0 25px #00d4ff,0 0 55px rgba(0,200,255,0.38)',transition:'box-shadow 0.4s ease'}}/>
          </div>
        </div>
        <div style={{...S.arcLabel,opacity:boot.title?1:0,transition:'opacity 0.9s ease'}}>J.A.R.V.I.S</div>
        <div style={{...S.arcSub,opacity:boot.title?1:0,transition:'opacity 0.9s ease'}}>MARK I — ONLINE</div>
      </div>

      {/* ── MKIII: AUTONOMOUS ALERTS — floating toasts top right ── */}
      <AutonomousAlerts/>

      {/* ── TICKER ── */}
      <AlertTicker visible={!!(boot.ticker&&shutStep<2)}/>

      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Share+Tech+Mono&display=swap');
        @keyframes spin1{from{transform:rotate(0deg)}to{transform:rotate(360deg)}}
        @keyframes spin2{from{transform:rotate(360deg)}to{transform:rotate(0deg)}}
        @keyframes pulse{0%,100%{opacity:1;box-shadow:0 0 38px #00b4ff,0 0 76px rgba(0,180,255,0.3)}50%{opacity:0.74;box-shadow:0 0 14px #00b4ff}}
        @keyframes blink{0%,100%{opacity:1}50%{opacity:0}}
        @keyframes cornerPulse{0%,100%{opacity:0.5}50%{opacity:1}}
        @keyframes bootScan{0%{top:-4px;opacity:1}100%{top:100vh;opacity:0}}
        @keyframes tickerScroll{0%{transform:translateX(0)}100%{transform:translateX(-50%)}}
        input::placeholder{color:rgba(0,100,160,0.42);font-family:'Share Tech Mono',monospace;}
        ::-webkit-scrollbar{width:0;}
        *{box-sizing:border-box;}
      `}</style>
    </div>
  )
}

export default HUD