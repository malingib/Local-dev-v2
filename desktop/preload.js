const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  getAppInfo: () => ipcRenderer.invoke('get-app-info'),
  selectDirectory: () => ipcRenderer.invoke('select-directory'),
  openDirectory: (dirPath) => ipcRenderer.invoke('open-directory', dirPath),
  notify: (title, body) => ipcRenderer.invoke('notify', { title, body }),
  getConfig: () => ipcRenderer.invoke('get-config'),
  saveConfig: (content) => ipcRenderer.invoke('save-config', content),

  // Guarded file ops from DATA_DIR only
  readProjectFile: (relativePath) => ipcRenderer.invoke('read-project-file', relativePath),
  writeProjectFile: (relativePath, content) => ipcRenderer.invoke('write-project-file', { relativePath, content }),
  deleteProjectFile: (relativePath) => ipcRenderer.invoke('delete-project-file', relativePath),
  listProjectDirectory: (relativePath) => ipcRenderer.invoke('list-project-directory', relativePath),

  // Navigation events from tray/menus
  onNavigate: (callback) => {
    const handler = (_event, route) => {
      window.dispatchEvent(new CustomEvent('electron:navigate', { detail: route }));
    };
    ipcRenderer.on('navigate', handler);
    return () => ipcRenderer.removeListener('navigate', handler);
  },
});
