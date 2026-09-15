/**
 * Electron main process.
 *
 * Creates the application window and points it at either the Vite dev
 * server (development) or the bundled static build (production).
 */

const { app, BrowserWindow } = require("electron");
const path = require("path");

const DEV_SERVER_URL = "http://localhost:5173";

function createWindow() {
  const window = new BrowserWindow({
    width: 1000,
    height: 700,
    webPreferences: {
      // Keep renderer code isolated from Node.js APIs - standard
      // Electron security practice.
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  const isDev = !app.isPackaged;

  if (isDev) {
    window.loadURL(DEV_SERVER_URL);
    window.webContents.openDevTools();
  } else {
    window.loadFile(path.join(__dirname, "../dist/index.html"));
  }
}

app.whenReady().then(() => {
  createWindow();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});