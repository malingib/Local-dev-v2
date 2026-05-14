const { app, BrowserWindow, Tray, Menu, nativeImage, Notification, ipcMain, dialog, shell } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');
const { createTray } = require('./tray');

let mainWindow = null;
let tray = null;
let backendProcess = null;
const isDev = process.env.NODE_ENV === 'development' || !app.isPackaged;

const DATA_DIR = path.join(app.getPath('userData'), 'codeaudit');
const SOUL_DIR = path.join(DATA_DIR, 'soul');
const WIKI_DIR = path.join(DATA_DIR, 'wiki');
const SKILLS_DIR = path.join(DATA_DIR, 'skills');
const BUDDY_DIR = path.join(DATA_DIR, 'buddy');
const SESSIONS_DIR = path.join(DATA_DIR, 'sessions');
const CONFIG_PATH = path.join(DATA_DIR, 'config.yaml');
const LOG_PATH = path.join(DATA_DIR, 'desktop.log');

function log(msg) {
  const line = `[${new Date().toISOString()}] ${msg}\n`;
  fs.appendFileSync(LOG_PATH, line);
}

function ensureDirs() {
  for (const dir of [DATA_DIR, SOUL_DIR, WIKI_DIR, SKILLS_DIR, BUDDY_DIR, SESSIONS_DIR]) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 900,
    minHeight: 600,
    title: 'CodeAudit Desktop',
    icon: path.join(__dirname, 'icons', 'icon.png'),
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
    show: false,
  });

  if (isDev) {
    mainWindow.loadURL('http://localhost:5173');
    mainWindow.webContents.openDevTools({ mode: 'detach' });
  } else {
    const distPath = path.join(__dirname, '..', 'app', 'dist', 'index.html');
    mainWindow.loadFile(distPath);
  }

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  mainWindow.on('minimize', (event) => {
    event.preventDefault();
    mainWindow.hide();
  });

  mainWindow.on('close', (event) => {
    if (tray) {
      event.preventDefault();
      mainWindow.hide();
    }
  });
}

function startBackend() {
  const backendDir = isDev
    ? path.join(__dirname, '..', 'codeaudit')
    : path.join(process.resourcesPath, 'backend');

  const env = {
    ...process.env,
    CODEAUDIT_DATA_DIR: DATA_DIR,
    CODEAUDIT_SOUL_DIR: SOUL_DIR,
    CODEAUDIT_WIKI_DIR: WIKI_DIR,
    CODEAUDIT_SKILLS_DIR: SKILLS_DIR,
    CODEAUDIT_BUDDY_DIR: BUDDY_DIR,
    CODEAUDIT_SESSIONS_DIR: SESSIONS_DIR,
    CODEAUDIT_CONFIG_PATH: CONFIG_PATH,
    PYTHONUNBUFFERED: '1',
  };

  const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';
  backendProcess = spawn(pythonCmd, ['-m', 'uvicorn', 'backend.api:app', '--host', '127.0.0.1', '--port', '8000'], {
    cwd: backendDir,
    env,
    stdio: ['pipe', 'pipe', 'pipe'],
  });

  backendProcess.stdout.on('data', (data) => {
    log(`[backend] ${data.toString().trim()}`);
  });

  backendProcess.stderr.on('data', (data) => {
    log(`[backend-err] ${data.toString().trim()}`);
  });

  backendProcess.on('exit', (code) => {
    log(`[backend] exited with code ${code}`);
    backendProcess = null;
  });

  backendProcess.on('error', (err) => {
    log(`[backend] error: ${err.message}`);
  });
}

function stopBackend() {
  if (backendProcess) {
    backendProcess.kill('SIGTERM');
    setTimeout(() => {
      if (backendProcess) backendProcess.kill('SIGKILL');
    }, 5000);
  }
}

function sendNotification(title, body) {
  if (Notification.isSupported()) {
    new Notification({ title, body, icon: path.join(__dirname, 'icons', 'icon.png') }).show();
  }
}

function setupIpc() {
  const backendBase = `http://127.0.0.1:8000`;
  ipcMain.handle('get-app-info', () => ({
    version: app.getVersion(),
    dataDir: DATA_DIR,
    soulDir: SOUL_DIR,
    wikiDir: WIKI_DIR,
    skillsDir: SKILLS_DIR,
    buddyDir: BUDDY_DIR,
    sessionsDir: SESSIONS_DIR,
    backendBase,
    isDev,
    platform: process.platform,
  }));

  ipcMain.handle('select-directory', async () => {
    const result = await dialog.showOpenDialog(mainWindow, {
      properties: ['openDirectory'],
    });
    return result.canceled ? null : result.filePaths[0];
  });

  ipcMain.handle('open-directory', (_, dirPath) => {
    shell.openPath(dirPath);
  });

  ipcMain.handle('notify', (_, { title, body }) => {
    sendNotification(title, body);
  });

  ipcMain.handle('get-config', () => {
    try {
      if (fs.existsSync(CONFIG_PATH)) {
        return fs.readFileSync(CONFIG_PATH, 'utf-8');
      }
      return null;
    } catch { return null; }
  });

  ipcMain.handle('save-config', (_, content) => {
    fs.writeFileSync(CONFIG_PATH, content, 'utf-8');
    return true;
  });

  function resolveSafePath(relativePath) {
    const resolved = path.resolve(DATA_DIR, relativePath);
    if (!resolved.startsWith(path.resolve(DATA_DIR))) {
      throw new Error('Access denied: path escapes data directory');
    }
    return resolved;
  }

  ipcMain.handle('read-project-file', (_, relativePath) => {
    try {
      const resolved = resolveSafePath(relativePath);
      if (fs.existsSync(resolved)) return fs.readFileSync(resolved, 'utf-8');
      return null;
    } catch { return null; }
  });

  ipcMain.handle('write-project-file', (_, { relativePath, content }) => {
    try {
      const resolved = resolveSafePath(relativePath);
      fs.mkdirSync(path.dirname(resolved), { recursive: true });
      fs.writeFileSync(resolved, content, 'utf-8');
      return true;
    } catch { return false; }
  });

  ipcMain.handle('delete-project-file', (_, relativePath) => {
    try {
      const resolved = resolveSafePath(relativePath);
      if (fs.existsSync(resolved)) fs.unlinkSync(resolved);
      return true;
    } catch { return false; }
  });

  ipcMain.handle('list-project-directory', (_, relativePath) => {
    try {
      const resolved = resolveSafePath(relativePath);
      if (!fs.existsSync(resolved)) return [];
      return fs.readdirSync(resolved, { withFileTypes: true }).map(d => ({
        name: d.name,
        isDirectory: d.isDirectory(),
        path: path.join(resolved, d.name),
      }));
    } catch { return []; }
  });
}

app.whenReady().then(() => {
  ensureDirs();
  setupIpc();
  createWindow();
  startBackend();
  tray = createTray(app, mainWindow);
  log('Desktop app started');
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    stopBackend();
    app.quit();
  }
});

app.on('before-quit', () => {
  stopBackend();
  if (tray) tray.destroy();
});

app.on('activate', () => {
  if (mainWindow) mainWindow.show();
});
