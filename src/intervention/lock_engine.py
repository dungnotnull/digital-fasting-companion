"""
Graduated 3-tier intervention lock engine.

Tier 1 (0.4-0.6): Desktop notification + mindfulness prompt
Tier 2 (0.6-0.8): Soft lock (apps minimized) + guided breathing exercise
Tier 3 (0.8-1.0): Hard lock (API firewall block) + real-world challenge required

The engine enforces cooldowns between tiers to prevent rapid re-triggering
and tracks intervention effectiveness through recovery logging.
"""

import json
import logging
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from threading import Lock
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class Tier(Enum):
    NONE = 0
    ONE = 1    # Nudge notification
    TWO = 2    # Soft lock
    THREE = 3  # Hard lock


class InterventionState(Enum):
    CLEAR = "clear"
    TIER_ACTIVE = "tier_active"
    CHALLENGE_PENDING = "challenge_pending"
    COOLDOWN = "cooldown"


@dataclass
class InterventionConfig:
    tier1_min: float = 0.4
    tier1_max: float = 0.6
    tier2_min: float = 0.6
    tier2_max: float = 0.8
    tier3_min: float = 0.8
    tier3_max: float = 1.0
    tier_cooldown_minutes: int = 15
    inter_tier_cooldown_minutes: int = 5


@dataclass
class InterventionEvent:
    tier: Tier
    fatigue_score: float
    timestamp: float = field(default_factory=time.time)
    session_id: Optional[str] = None
    trigger_category: Optional[str] = None
    resolved: bool = False
    resolution_type: Optional[str] = None


class LockEngine:
    """
    Graduated intervention engine.

    Manages the full intervention lifecycle:
    1. Receives fatigue scores and determines tier
    2. Applies the appropriate lock mechanism
    3. Tracks cooldowns
    4. Releases locks on challenge completion
    """

    def __init__(
        self,
        config: Optional[InterventionConfig] = None,
        categories_path: str = "config/categories.json",
    ):
        self.config = config or InterventionConfig()
        self.categories_path = Path(categories_path)

        self.state: InterventionState = InterventionState.CLEAR
        self.active_tier: Tier = Tier.NONE
        self.active_event: Optional[InterventionEvent] = None
        self.last_intervention_time: float = 0
        self.last_challenge_time: float = 0

        self._lock = Lock()
        self._firewall_rules_applied: List[str] = []

        self._block_domains: List[str] = []
        self._load_categories()

        logger.info("LockEngine initialized (state=%s)", self.state.value)

    def _load_categories(self) -> None:
        if self.categories_path.exists():
            try:
                with open(self.categories_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._block_domains = data.get("domain_blocklist", [])
                logger.info("Loaded %d block domains", len(self._block_domains))
            except Exception as e:
                logger.warning("Failed to load categories: %s", e)

    def evaluate(self, fatigue_score: float) -> Tier:
        """
        Determine intervention tier from fatigue score.

        Returns:
            Tier.ONE, Tier.TWO, Tier.THREE, or Tier.NONE
        """
        if self.config.tier3_min <= fatigue_score <= self.config.tier3_max:
            return Tier.THREE
        if self.config.tier2_min <= fatigue_score <= self.config.tier2_max:
            return Tier.TWO
        if self.config.tier1_min <= fatigue_score <= self.config.tier1_max:
            return Tier.ONE
        return Tier.NONE

    def can_intervene(self, tier: Tier) -> bool:
        """Check if intervention is allowed considering cooldowns."""
        now = time.time()

        if self.state == InterventionState.CHALLENGE_PENDING:
            return False

        if self.state == InterventionState.COOLDOWN:
            if now - self.last_intervention_time < self.config.tier_cooldown_minutes * 60:
                return False

        if self.state == InterventionState.TIER_ACTIVE:
            if self.active_tier.value >= tier.value:
                if now - self.last_intervention_time < self.config.inter_tier_cooldown_minutes * 60:
                    return False

        return True

    def apply_intervention(
        self,
        fatigue_score: float,
        session_id: Optional[str] = None,
        trigger_category: Optional[str] = None,
    ) -> InterventionEvent:
        """
        Apply the appropriate intervention for the given fatigue score.

        Returns:
            InterventionEvent describing what was applied
        """
        tier = self.evaluate(fatigue_score)
        event = InterventionEvent(
            tier=tier,
            fatigue_score=fatigue_score,
            session_id=session_id,
            trigger_category=trigger_category,
        )

        if tier == Tier.NONE:
            self._restore_all()
            return event

        if not self.can_intervene(tier):
            logger.debug("Intervention blocked by cooldown (tier=%s)", tier.name)
            return event

        with self._lock:
            self.active_tier = tier
            self.active_event = event
            self.last_intervention_time = time.time()

            if tier == Tier.ONE:
                self._apply_tier1(event)
            elif tier == Tier.TWO:
                self._apply_tier2(event)
            elif tier == Tier.THREE:
                self._apply_tier3(event)

        return event

    def _apply_tier1(self, event: InterventionEvent) -> None:
        """Tier 1: Desktop notification + mindfulness prompt."""
        self.state = InterventionState.TIER_ACTIVE
        logger.info(
            "TIER 1 applied: nudge notification (score=%.2f)", event.fatigue_score
        )
        self._show_notification(
            "Digital Fasting",
            "You've been online for a while. Take a moment to breathe?"
        )

    def _apply_tier2(self, event: InterventionEvent) -> None:
        """Tier 2: Soft lock - minimize apps + breathing exercise."""
        self.state = InterventionState.TIER_ACTIVE
        logger.info(
            "TIER 2 applied: soft lock (score=%.2f)", event.fatigue_score
        )
        self._minimize_apps()
        self._show_notification(
            "Digital Fasting - Soft Lock",
            "Your apps have been minimized. Try a 2-minute breathing exercise:\n"
            "Breathe in for 4 seconds, hold for 4, out for 6. Repeat."
        )

    def _apply_tier3(self, event: InterventionEvent) -> None:
        """Tier 3: Hard lock - block API domains + require challenge."""
        self.state = InterventionState.CHALLENGE_PENDING
        logger.info(
            "TIER 3 applied: hard lock (score=%.2f)", event.fatigue_score
        )
        self._block_api_domains()
        self._show_notification(
            "Digital Fasting - Hard Lock",
            "You've reached your digital limit. API access has been restricted.\n"
            "Complete a real-world challenge to restore access."
        )

    def resolve_intervention(
        self, resolution_type: str = "challenge_completed"
    ) -> Optional[InterventionEvent]:
        """
        Resolve the active intervention and restore access.

        Args:
            resolution_type: How the intervention was resolved
                ('challenge_completed', 'timeout', 'manual')

        Returns:
            The resolved event, or None
        """
        if self.state == InterventionState.CLEAR:
            return None

        with self._lock:
            if self.active_event:
                self.active_event.resolved = True
                self.active_event.resolution_type = resolution_type

            self._restore_all()
            self.state = InterventionState.COOLDOWN
            self.last_challenge_time = time.time()

            event = self.active_event
            self.active_event = None

            logger.info("Intervention resolved (type=%s)", resolution_type)
            return event

    def _restore_all(self) -> None:
        """Restore all system state (remove blocks, restore windows)."""
        self._remove_firewall_rules()
        self.state = InterventionState.CLEAR
        self.active_tier = Tier.NONE

    # ── OS-level operations ────────────────────────────────────────

    def _show_notification(self, title: str, message: str) -> None:
        """Show a desktop notification (cross-platform stub)."""
        system = sys.platform
        try:
            if system == "win32":
                self._notify_windows(title, message)
            elif system == "darwin":
                self._notify_macos(title, message)
            else:
                self._notify_linux(title, message)
        except Exception as e:
            logger.warning("Failed to show notification: %s", e)

    def _notify_windows(self, title: str, message: str) -> None:
        try:
            from win10toast import ToastNotifier
            toaster = ToastNotifier()
            toaster.show_toast(title, message, duration=5, threaded=True)
        except ImportError:
            logger.debug("win10toast not available, skipping notification")

    def _notify_macos(self, title: str, message: str) -> None:
        subprocess.run(
            ["osascript", "-e",
             f'display notification "{message}" with title "{title}"'],
            capture_output=True,
        )

    def _notify_linux(self, title: str, message: str) -> None:
        subprocess.run(
            ["notify-send", title, message], capture_output=True
        )

    def _minimize_apps(self) -> None:
        """Minimize all windows (platform-specific)."""
        system = sys.platform
        try:
            if system == "win32":
                import ctypes
                ctypes.windll.user32.keybd_event(0x5B, 0, 0, 0)  # Left Windows
                ctypes.windll.user32.keybd_event(0x4D, 0, 0, 0)  # M key
                ctypes.windll.user32.keybd_event(0x4D, 0, 2, 0)  # Release M
                ctypes.windll.user32.keybd_event(0x5B, 0, 2, 0)  # Release Win
            elif system == "darwin":
                subprocess.run([
                    "osascript", "-e",
                    'tell application "System Events" to keystroke "m" using {command down, option down}'
                ], capture_output=True)
        except Exception as e:
            logger.warning("Failed to minimize apps: %s", e)

    def _block_api_domains(self) -> None:
        """Block AI/Social media API domains via OS firewall."""
        if not self._block_domains:
            logger.debug("No domains to block")
            return

        system = sys.platform
        blocked = 0
        for domain in self._block_domains:
            try:
                if system == "win32":
                    self._block_domain_windows(domain)
                elif system == "darwin":
                    self._block_domain_macos(domain)
                blocked += 1
            except Exception as e:
                logger.debug("Failed to block %s: %s", domain, e)

        if blocked > 0:
            logger.info("Blocked %d domains via firewall", blocked)

    def _block_domain_windows(self, domain: str) -> None:
        rule_name = f"digital-fasting-block-{domain.replace('.', '-')}"
        check = subprocess.run(
            ["netsh", "advfirewall", "firewall", "show", "rule", f"name={rule_name}"],
            capture_output=True, text=True
        )
        if "No rules match" in check.stdout or check.returncode != 0:
            subprocess.run([
                "netsh", "advfirewall", "firewall", "add", "rule",
                f"name={rule_name}",
                "dir=out", "action=block",
                f"remoteip={domain}", "enable=yes"
            ], capture_output=True)
            self._firewall_rules_applied.append(rule_name)

    def _block_domain_macos(self, domain: str) -> None:
        rule_name = f"digital-fasting-block-{domain.replace('.', '-')}"
        check = subprocess.run(
            ["pfctl", "-s", "rules"], capture_output=True, text=True
        )
        if rule_name not in check.stdout:
            with open("/tmp/digital_fasting_pf.conf", "a") as f:
                f.write(f"block drop out quick from any to {domain}\n")
            subprocess.run(
                ["pfctl", "-f", "/tmp/digital_fasting_pf.conf"], capture_output=True
            )
            self._firewall_rules_applied.append(rule_name)

    def _remove_firewall_rules(self) -> None:
        """Remove all applied firewall rules."""
        system = sys.platform
        for rule_name in self._firewall_rules_applied:
            try:
                if system == "win32":
                    subprocess.run([
                        "netsh", "advfirewall", "firewall", "delete", "rule",
                        f"name={rule_name}"
                    ], capture_output=True)
            except Exception as e:
                logger.debug("Failed to remove rule %s: %s", rule_name, e)

        if self._firewall_rules_applied:
            logger.info("Removed %d firewall rules", len(self._firewall_rules_applied))
        self._firewall_rules_applied = []

    # ── Properties ─────────────────────────────────────────────────

    @property
    def is_locked(self) -> bool:
        return self.state == InterventionState.CHALLENGE_PENDING

    @property
    def is_soft_locked(self) -> bool:
        return self.state == InterventionState.TIER_ACTIVE and self.active_tier == Tier.TWO

    @property
    def requires_challenge(self) -> bool:
        return self.state == InterventionState.CHALLENGE_PENDING
