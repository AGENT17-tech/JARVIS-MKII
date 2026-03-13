const { app, BrowserWindow, ipcMain } = require('electron')
const path = require('path')
const si = require('systeminformation')

let mainWindow

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1920,
    height: 1080,
    frame: false,
    transparent: true,
    alwaysOnTop: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  })

  mainWindow.loadURL('http://localhost:5173')
  mainWindow.setIgnoreMouseEvents(false)
}

app.whenReady().then(createWindow)

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})

setInterval(async () => {
  if (!mainWindow) return
  const [cpu, mem, temp] = await Promise.all([
    si.currentLoad(),
    si.mem(),
    si.cpuTemperature()
  ])
  mainWindow.webContents.send('system-stats', {
    cpu: Math.round(cpu.currentLoad),
    ram: Math.round((mem.used / mem.total) * 100),
    temp: Math.round(temp.main) || 0
  })
}, 2000)