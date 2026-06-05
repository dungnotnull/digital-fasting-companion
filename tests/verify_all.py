"""Deep functional verification of all components."""
import os, sys, time, json

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

passed = 0
failed = 0

def check(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  [PASS] {name} {detail}")
    else:
        failed += 1
        print(f"  [FAIL] {name} {detail}")

print("=" * 60)
print("Digital Fasting Companion - Full Functional Verification")
print("=" * 60)

# 1. Settings
from src.config.settings import Settings
s = Settings()
check("Settings load", s.app_name == "digital-fasting-companion", f"app={s.app_name}")
check("Settings tiers", s.intervention.tier3_min_score == 0.8, f"t3_min={s.intervention.tier3_min_score}")

# 2. LocalDB
from src.storage.local_db import LocalDB
db_path = 'data/test_verify.db'
if os.path.exists(db_path): os.remove(db_path)
db = LocalDB(db_path, 'test-key-12345')
db.connect()
db.init_schema()
db.set_setting('test', 'hello')
check("DB write", db.get_setting('test') == 'hello')
sid = db.insert_session('chatgpt', 'ai_tools', int(time.time()), 300)
sessions = db.get_sessions(limit=5)
check("DB session insert", len(sessions) >= 1, f"count={len(sessions)}")
eid = db.insert_fatigue_event('tier3', 0.85, session_id=sid, trigger_category='ai_tools')
events = db.get_recent_events(5)
check("DB events insert", len(events) >= 1, f"count={len(events)}")
cid = db.insert_challenge('physical', 'Test Challenge', 'Test desc', 'static', event_id=eid)
db.complete_challenge(cid, rating=5)
db.disconnect()
os.remove(db_path)

# 3. ScreenTimeMonitor
from src.monitor.screen_time import ScreenTimeMonitor, AppCategory
stm = ScreenTimeMonitor()
check("ScreenTime AI categorization", stm._categorize_app('chatgpt') == AppCategory.AI_TOOLS)
check("ScreenTime unknown", stm._categorize_app('zzzapp1234') == AppCategory.UNKNOWN)

# 4. KeystrokeTracker
from src.monitor.keystroke import KeystrokeTracker
kt = KeystrokeTracker()
features = kt.get_features()
check("Keystroke features", len(features) == 3, str(features))

# 5. MLFatigueDetector
from src.detector.ml_fatigue_detector import MLFatigueDetector
mld = MLFatigueDetector()
low = mld.predict_score(typing_wpm=50, error_rate=0.02, backspace_ratio=0.03, session_duration_min=10, app_switch_rate=1, hour_of_day=10)
high = mld.predict_score(typing_wpm=15, error_rate=0.20, backspace_ratio=0.25, session_duration_min=150, app_switch_rate=12, hour_of_day=23)
check("MLDetector range", 0 <= low <= 1 and 0 <= high <= 1, f"low={low:.3f} high={high:.3f}")
check("MLDetector ordering", high > low, f"high={high:.3f} > low={low:.3f}")

# 6. FeaturePipeline
from src.detector.feature_pipeline import FeaturePipeline
fp = FeaturePipeline(window_size=5)
for i in range(10):
    fp.add_raw_signals(typing_wpm=40, error_rate=0.05, backspace_ratio=0.08, session_duration_min=30, current_app_name='vscode')
fv = fp.compute()
check("FeaturePipeline compute", fv.typing_wpm > 0, f"wpm={fv.typing_wpm:.1f}")

# 7. BaselineCollector
from src.detector.baseline_collector import BaselineCollector
bc = BaselineCollector(storage_path='data/test_baseline.json')
bc.start()
bc.record_sample(fv, fatigue_label=0.3)
bc.record_label(0.6)
bc.stop()
check("BaselineCollector count", bc.sample_count >= 1, f"n={bc.sample_count}")
if os.path.exists('data/test_baseline.json'): os.remove('data/test_baseline.json')

# 8. LockEngine tiers
from src.intervention.lock_engine import LockEngine, Tier, InterventionConfig
le = LockEngine(config=InterventionConfig(), categories_path='config/categories.json')
check("Tier NONE", le.evaluate(0.2) == Tier.NONE)
check("Tier ONE", le.evaluate(0.5) == Tier.ONE)
check("Tier TWO", le.evaluate(0.75) == Tier.TWO)
check("Tier THREE", le.evaluate(0.9) == Tier.THREE)

# 9. BreathingTimer
from src.intervention.breathing_timer import BreathingTimer
bt = BreathingTimer()
check("BreathingTimer cycles", bt.TOTAL_CYCLES == 8)

# 10. StaticPool
from src.agent.static_pool import StaticChallengePool
sp = StaticChallengePool()
ch = sp.get_random()
check("StaticPool challenge", ch is not None, f"title={ch.title[:40]}...")
check("StaticPool category", ch.category in ['physical','creative','social','introspective'])

# 11. UserContext
from src.agent.user_context import UserContext
ctx = UserContext(time_of_day=14, fatigue_score=0.7, session_duration_minutes=90)
check("UserContext period", ctx.get_time_period() in ['morning','afternoon','evening','night'], ctx.get_time_period())
check("UserContext category", ctx.get_suggested_category() in ['physical','creative','social','introspective'], ctx.get_suggested_category())

# 12. QualityTracker
from src.agent.quality_tracker import ChallengeQualityTracker
qt = ChallengeQualityTracker(storage_path='data/test_ratings.json')
qt.record_rating('ch-1', 4, 'static', 'physical')
qt.record_rating('ch-2', 5, 'ollama', 'creative')
avg = qt.average_rating()
check("QualityTracker avg", 4 <= avg <= 5, f"avg={avg:.1f}")
if os.path.exists('data/test_ratings.json'): os.remove('data/test_ratings.json')

# 13. Rate limiter
from src.agent.claude_backend import RateLimiter
rl = RateLimiter(max_calls=10)
check("RateLimiter allow", rl.can_call())
rl.record_call()
check("RateLimiter count", rl.calls_today == 1)

# 14. Claude/OpenAI stubs
from src.agent.claude_backend import ClaudeBackend
from src.agent.openai_backend import OpenAIBackend
check("Claude stub", not ClaudeBackend(api_key=None).is_available())
check("OpenAI stub", not OpenAIBackend(api_key=None).is_available())

# 15. KeyManager
from src.config.key_manager import get_key_manager
km = get_key_manager()
check("KeyManager service", km.service == 'digital-fasting-companion')

# 16. Biometrics
from src.biometrics.garmin_backend import BiometricReading
br = BiometricReading(hrv_score=70, stress_score=30)
feat = br.to_fatigue_feature()
check("Biometrics feature", 0 <= feat <= 100, f"value={feat:.1f}")

# 17. Relevance scorer
from src.knowledge.relevance_scorer import RelevanceScorer
rs = RelevanceScorer()
s1 = rs.score('cognitive fatigue in digital workers', 'Studies cognitive fatigue from screen time and digital wellbeing interventions.')
s2 = rs.score('quantum computing advances', 'Discusses quantum error correction and superconducting qubits.')
check("RelevanceScorer order", s1 > s2, f"relevant={s1:.2f} > irrelevant={s2:.2f}")

# 18. FeatureVector round-trip
from src.detector.feature_pipeline import FeatureVector
fv2 = FeatureVector(typing_wpm=35, error_rate=0.08, backspace_ratio=0.12, session_duration_min=45, app_switch_rate=3, hour_of_day=15, hrv_score=55)
d = fv2.to_dict()
fv3 = FeatureVector.from_dict(d)
check("FeatureVector round-trip", fv3.typing_wpm == 35 and fv3.error_rate == 0.08)

# 19. Scheduler
from src.scheduler import TaskScheduler
ts = TaskScheduler()
check("Scheduler init", not ts.is_running)

# 20. SystemTray
from src.ui.system_tray import SystemTrayApp
sta = SystemTrayApp()
check("SystemTray init", not sta._running)

# 21. ChallengeGenerator E2E
from src.agent.router import ChallengeGenerator
cg = ChallengeGenerator()
challenge = cg.get_challenge(session_min=90, fatigue_score=0.7, time_of_day=18)
check("ChallengeGenerator e2e", challenge is not None, f"title={challenge.title[:40]}... source={challenge.source}")
check("Challenge quality tracking", cg.generation_count >= 1, f"count={cg.generation_count}")
cg.record_rating(challenge.id, 5)
check("Challenge rating", cg.quality_tracker.total_ratings >= 1)

# 22. Ollama health check (must fail = no local ollama)
from src.agent.ollama_backend import OllamaBackend
ollama = OllamaBackend(host="http://localhost:11434", timeout=2)
check("Ollama health (expected: unavailable)", not ollama.is_available())

# 23. Fallback chain verification
backends = cg.get_available_backends()
check("Fallback chain exists", len(backends) >= 1, str(backends))
check("StaticPool always available", 'StaticChallengePool' in backends)

# 24. Knowledge crawler state (no network — offline check only)
from src.knowledge.crawler import KnowledgeCrawler
kc = KnowledgeCrawler(storage_path='data/test_crawler.json')
check("Crawler init", kc.known_papers_count >= 0)
# Don't call kc.run() — it makes real HTTP requests to ArXiv/Semantic Scholar
check("Crawler state persistent", isinstance(kc._known_dois, set))
if os.path.exists('data/test_crawler.json'): os.remove('data/test_crawler.json')

# 25. Main entry point
import importlib
spec = importlib.util.spec_from_file_location("__main__", "src/main.py")
check("Main.py loadable", spec is not None)

print()
print("=" * 60)
print(f"RESULTS: {passed} passed, {failed} failed out of {passed + failed}")
print("=" * 60)
if failed > 0:
    sys.exit(1)
