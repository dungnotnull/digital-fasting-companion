// Digital Fasting Companion — Background Service Worker
// Tracks AI tool and social media tab usage, manages intervention state,
// and communicates with the desktop daemon via Native Messaging.

const AI_DOMAINS = [
  'openai.com', 'anthropic.com', 'claude.ai', 'bard.google.com',
  'chat.openai.com', 'perplexity.ai', 'poe.com', 'you.com',
];

const SOCIAL_DOMAINS = [
  'facebook.com', 'twitter.com', 'x.com', 'instagram.com',
  'tiktok.com', 'youtube.com', 'reddit.com', 'linkedin.com',
  'discord.com', 'telegram.org', 'twitch.tv',
];

const TRACKED_DOMAINS = [...AI_DOMAINS, ...SOCIAL_DOMAINS];

let activeTimerId = null;
let sessionStartTime = null;
let currentDomain = null;
let currentCategory = null;
let totalAiSeconds = 0;
let totalSocialSeconds = 0;
let interventionActive = false;
let nativePort = null;

// ---- Domain Classification ----

function classifyDomain(url) {
  if (!url) return null;
  const hostname = new URL(url).hostname.replace('www.', '');
  for (const domain of AI_DOMAINS) {
    if (hostname.includes(domain)) return { domain: hostname, category: 'ai_tools' };
  }
  for (const domain of SOCIAL_DOMAINS) {
    if (hostname.includes(domain)) return { domain: hostname, category: 'social_media' };
  }
  return null;
}

// ---- Session Tracking ----

function startSession(domain, category) {
  stopSession();
  currentDomain = domain;
  currentCategory = category;
  sessionStartTime = Date.now();
  activeTimerId = setInterval(tickSession, 10000); // every 10s
  console.log(`[DF] Session started: ${domain} (${category})`);
}

function stopSession() {
  if (activeTimerId) {
    clearInterval(activeTimerId);
    activeTimerId = null;
  }
  if (sessionStartTime && currentCategory) {
    const duration = Math.floor((Date.now() - sessionStartTime) / 1000);
    if (currentCategory === 'ai_tools') totalAiSeconds += duration;
    else if (currentCategory === 'social_media') totalSocialSeconds += duration;
  }
  sessionStartTime = null;
  currentDomain = null;
  currentCategory = null;
}

function tickSession() {
  if (!sessionStartTime || !currentCategory) return;
  const duration = Math.floor((Date.now() - sessionStartTime) / 1000);
  const currentTotal = currentCategory === 'ai_tools' ? totalAiSeconds + duration : totalSocialSeconds + duration;

  // Send usage update to desktop daemon
  if (nativePort) {
    try {
      nativePort.postMessage({
        type: 'usage_update',
        category: currentCategory,
        domain: currentDomain,
        session_seconds: duration,
        ai_total_seconds: currentCategory === 'ai_tools' ? currentTotal : totalAiSeconds,
        social_total_seconds: currentCategory === 'social_media' ? currentTotal : totalSocialSeconds,
        timestamp: Date.now(),
      });
    } catch (e) {
      console.warn('[DF] Native messaging send failed:', e);
    }
  }
}

// ---- Tab Management ----

chrome.tabs.onActivated.addListener((activeInfo) => {
  chrome.tabs.get(activeInfo.tabId, (tab) => {
    handleTabChange(tab);
  });
});

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.url || changeInfo.status === 'complete') {
    handleTabChange(tab);
  }
});

chrome.webNavigation.onCommitted.addListener((details) => {
  if (details.frameId === 0) {
    handleUrlChange(details.url);
  }
});

function handleTabChange(tab) {
  if (!tab.url) return;
  handleUrlChange(tab.url);
}

function handleUrlChange(url) {
  const classified = classifyDomain(url);
  if (classified) {
    if (classified.domain !== currentDomain) {
      startSession(classified.domain, classified.category);
    }
  } else {
    if (currentDomain) {
      stopSession();
    }
  }
}

// ---- Native Messaging ----

function connectNative() {
  const hostName = 'com.digitalfasting.companion';
  try {
    nativePort = chrome.runtime.connectNative(hostName);
    nativePort.onMessage.addListener(handleNativeMessage);
    nativePort.onDisconnect.addListener(() => {
      console.log('[DF] Native host disconnected');
      nativePort = null;
      // Retry after 30s
      setTimeout(connectNative, 30000);
    });
    console.log('[DF] Native messaging connected');
  } catch (e) {
    console.warn('[DF] Native messaging not available:', e.message);
  }
}

function handleNativeMessage(msg) {
  if (msg.type === 'intervention') {
    handleIntervention(msg.tier, msg.challenge);
  } else if (msg.type === 'status_request') {
    sendStatus();
  }
}

// ---- Intervention Handling ----

function handleIntervention(tier, challenge) {
  interventionActive = true;
  stopSession();

  if (tier === 3 && challenge) {
    // Show overlay on all tracked tabs
    chrome.tabs.query({}, (tabs) => {
      for (const tab of tabs) {
        const classified = classifyDomain(tab.url);
        if (classified) {
          chrome.tabs.sendMessage(tab.id, {
            type: 'show_overlay',
            challenge: challenge,
          }).catch(() => {});
        }
      }
    });
  }

  // Notify popup
  chrome.runtime.sendMessage({
    type: 'intervention_active',
    tier: tier,
    challenge: challenge || null,
  }).catch(() => {});
}

function sendStatus() {
  if (nativePort) {
    try {
      nativePort.postMessage({
        type: 'browser_status',
        ai_seconds: totalAiSeconds,
        social_seconds: totalSocialSeconds,
        active_session: currentDomain,
        intervention_active: interventionActive,
      });
    } catch (e) {}
  }
}

// ---- Message Handling ----

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.action === 'get_status') {
    sendResponse({
      ai_seconds: totalAiSeconds,
      social_seconds: totalSocialSeconds,
      active_session: currentDomain,
      intervention_active: interventionActive,
    });
  } else if (msg.action === 'challenge_complete') {
    interventionActive = false;
    if (nativePort) {
      nativePort.postMessage({ type: 'challenge_completed' });
    }
    sendResponse({ success: true });
  } else if (msg.action === 'challenge_snooze') {
    interventionActive = false;
    if (nativePort) {
      nativePort.postMessage({ type: 'challenge_snoozed' });
    }
  }
  return true;
});

// ---- Init ----

connectNative();
