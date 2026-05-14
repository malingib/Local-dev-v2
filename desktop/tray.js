const { Tray, Menu, nativeImage, app } = require('electron');
const path = require('path');

function createTray(appInstance, mainWindow) {
  const iconPath = path.join(__dirname, 'icons', 'icon.png');
  let trayIcon;
  try {
    trayIcon = nativeImage.createFromPath(iconPath).resize({ width: 16, height: 16 });
  } catch {
    trayIcon = nativeImage.createEmpty();
  }

  const tray = new Tray(trayIcon);
  tray.setToolTip('CodeAudit Desktop');

  const contextMenu = Menu.buildFromTemplate([
    {
      label: 'Show CodeAudit',
      click: () => {
        if (mainWindow) {
          mainWindow.show();
          mainWindow.focus();
        }
      },
    },
    { type: 'separator' },
    {
      label: 'New Session',
      click: () => {
        if (mainWindow) {
          mainWindow.show();
          mainWindow.focus();
          mainWindow.webContents.send('navigate', '/');
        }
      },
    },
    { type: 'separator' },
    {
      label: 'Settings',
      click: () => {
        if (mainWindow) {
          mainWindow.show();
          mainWindow.focus();
          mainWindow.webContents.send('navigate', '/settings');
        }
      },
    },
    { type: 'separator' },
    {
      label: 'Quit',
      click: () => {
        appInstance.quit();
      },
    },
  ]);

  tray.setContextMenu(contextMenu);

  tray.on('double-click', () => {
    if (mainWindow) {
      if (mainWindow.isVisible()) {
        mainWindow.focus();
      } else {
        mainWindow.show();
      }
    }
  });

  return tray;
}

module.exports = { createTray };
