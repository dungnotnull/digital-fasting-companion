// Content script — injected into tracked AI/social media pages.
// Provides soft lock overlay UI when intervention is active.

let overlayElement = null;

function createOverlay(challenge) {
  if (overlayElement) return;

  overlayElement = document.createElement('div');
  overlayElement.id = 'df-overlay';
  overlayElement.innerHTML = `
    <style>
      #df-overlay {
        position: fixed; top: 0; left: 0; right: 0; bottom: 0;
        background: rgba(13, 17, 23, 0.95);
        z-index: 999999;
        display: flex; align-items: center; justify-content: center;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      }
      #df-overlay .card {
        background: #161b22; border: 1px solid #30363d;
        border-radius: 12px; padding: 32px; max-width: 480px;
        text-align: center; color: #c9d1d9;
      }
      #df-overlay .badge {
        display: inline-block; background: #da3633; color: #fff;
        padding: 4px 14px; border-radius: 20px; font-size: 12px;
        font-weight: 600; margin-bottom: 16px;
      }
      #df-overlay h2 { color: #f0f6fc; margin-bottom: 8px; font-size: 20px; }
      #df-overlay .desc { color: #8b949e; font-size: 14px; line-height: 1.6; margin-bottom: 24px; }
      #df-overlay .challenge-box {
        background: #21262d; border: 1px solid #30363d;
        border-radius: 8px; padding: 20px; margin-bottom: 24px;
        text-align: left;
      }
      #df-overlay .challenge-box .cat { font-size: 11px; text-transform: uppercase; color: #8b949e; }
      #df-overlay .challenge-box .title { font-size: 16px; font-weight: 600; color: #f0f6fc; margin: 6px 0; }
      #df-overlay .btn {
        padding: 10px 28px; border-radius: 6px; font-size: 14px;
        font-weight: 600; cursor: pointer; border: none;
      }
      #df-overlay .btn-done { background: #238636; color: #fff; margin-right: 8px; }
      #df-overlay .btn-done:hover { background: #2ea043; }
      #df-overlay .btn-snooze { background: #21262d; color: #c9d1d9; border: 1px solid #30363d; }
      #df-overlay .btn-snooze:hover { background: #30363d; }
    </style>
    <div class="card">
      <div class="badge">Digital Fasting — Hard Lock</div>
      <h2>Time for a Real-World Break</h2>
      <p class="desc">You've reached your digital limit. Complete the challenge below to restore access.</p>
      <div class="challenge-box">
        <div class="cat">${challenge.category || 'physical'}</div>
        <div class="title">${challenge.title || 'Take a mindful break'}</div>
        <p class="desc" style="margin-bottom:0;">${challenge.description || ''}</p>
      </div>
      <button class="btn btn-done" id="df-complete-btn">I Completed the Challenge</button>
      <button class="btn btn-snooze" id="df-snooze-btn">Snooze (5 min)</button>
    </div>
  `;

  document.body.appendChild(overlayElement);

  document.getElementById('df-complete-btn').addEventListener('click', () => {
    chrome.runtime.sendMessage({ action: 'challenge_complete' }, () => {
      removeOverlay();
    });
  });

  document.getElementById('df-snooze-btn').addEventListener('click', () => {
    chrome.runtime.sendMessage({ action: 'challenge_snooze' });
    removeOverlay();
  });
}

function removeOverlay() {
  if (overlayElement) {
    overlayElement.remove();
    overlayElement = null;
  }
}

// Listen for intervention triggers
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === 'show_overlay' && msg.challenge) {
    createOverlay(msg.challenge);
  }
  sendResponse({ received: true });
});
