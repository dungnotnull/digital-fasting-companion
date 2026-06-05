// Popup script — fetches status from background and updates UI.

document.addEventListener('DOMContentLoaded', () => {
  chrome.runtime.sendMessage({ action: 'get_status' }, (status) => {
    updateUI(status);
  });
});

function updateUI(status) {
  if (!status) return;

  // Time display
  const aiH = Math.floor(status.ai_seconds / 3600);
  const aiM = Math.floor((status.ai_seconds % 3600) / 60);
  document.getElementById('aiTime').textContent = `${aiH}h ${aiM}m`;

  const socH = Math.floor(status.social_seconds / 3600);
  const socM = Math.floor((status.social_seconds % 3600) / 60);
  document.getElementById('socialTime').textContent = `${socH}h ${socM}m`;

  // Status bar
  const bar = document.getElementById('statusBar');
  if (status.intervention_active) {
    bar.className = 'status-bar locked';
    bar.textContent = 'Locked — Challenge Required';
  } else if (status.ai_seconds > 7200 || status.social_seconds > 10800) {
    bar.className = 'status-bar warning';
    bar.textContent = 'High Usage — Take a Break';
  } else {
    bar.className = 'status-bar active';
    bar.textContent = 'Monitoring';
  }
}

// Button handlers
document.getElementById('dashboardBtn').addEventListener('click', () => {
  chrome.tabs.create({ url: chrome.runtime.getURL('popup.html') });
});

document.getElementById('settingsBtn').addEventListener('click', () => {
  chrome.runtime.openOptionsPage ? chrome.runtime.openOptionsPage() : null;
});
