#!/usr/bin/env bash
# Drives the full ElectroCalc first-run/admin/authentication journey on a
# booted Android emulator and verifies the device database at every phase.
# Required environment: ADB (path to adb), APK (release APK to install),
# OUT (output directory for screenshots and reports).
set -uxo pipefail

: "${ADB:?ADB must point to the adb binary}"
: "${APK:?APK must point to the release apk}"
OUT="${OUT:-$PWD}"
PKG=com.electrocalc.app
ACT="$PKG/org.kivy.android.PythonActivity"

mkdir -p "$OUT"
cd "$OUT"

fail() {
  echo "::error title=journey::FAILED: $*"
  echo "[journey] FAILED: $*"
  echo "::error title=journey-counts::submit=$(log_count 'login_submit') ok=$(log_count 'login=ok') denied=$(log_count 'login=denied') dash=$(log_count 'screen=dashboard') start=$(log_count 'app_start') focus_user=$(log_count 'focus=username') focus_pass=$(log_count 'focus=password')"
  pull_db db-failure >/dev/null 2>&1 || true
  # Surface the failure context as annotations so diagnosis works even when
  # logs and artifacts are unavailable.
  [ -f db-timeline.txt ] && tail -n 3 db-timeline.txt | cut -c1-240 | while IFS= read -r line; do
    echo "::error title=journey-db::${line}"
  done
  kivy_log | tail -n 6 | cut -c1-240 | while IFS= read -r line; do
    echo "::error title=journey-klog::${line}"
  done
  exit 1
}
phase() { echo "::notice title=journey::${1}"; }

shot() { timeout 60 "$ADB" exec-out screencap -p > "$1" || true; }
tap() { "$ADB" shell input tap "$1" "$2" >/dev/null 2>&1 || true; sleep "${3:-1}"; }
typ() { "$ADB" shell input text "$1" >/dev/null 2>&1 || true; sleep 1; }
keyboard_shown() {
  local n
  n=$("$ADB" shell dumpsys input_method 2>/dev/null | grep -acE 'mInputShown=true|mIsInputViewShown=true')
  [ "${n:-0}" -gt 0 ]
}
hide_keyboard() {
  local i=0
  while keyboard_shown && [ "$i" -lt 3 ]; do
    "$ADB" shell input keyevent 4 >/dev/null 2>&1 || true
    sleep 1
    i=$((i+1))
  done
}
disable_imes() {
  local ime
  for ime in $("$ADB" shell ime list -s 2>/dev/null | tr -d '\r'); do
    "$ADB" shell ime disable "$ime" >/dev/null 2>&1 || true
  done
}
clear_field() {
  "$ADB" shell 'input keyevent 123; i=0; while [ $i -lt 24 ]; do input keyevent 67; i=$((i+1)); done' >/dev/null 2>&1 || true
  sleep 1
}
fill_field() {
  # A visible soft keyboard resizes the Kivy window and moves every widget, so
  # the tap coordinates are only valid while it is hidden.
  hide_keyboard
  tap "$1" "$2" 1
  clear_field
  typ "$3"
  hide_keyboard
}
fill_login() {
  # The login screen keeps the username across attempts; refill both anyway
  # so a stale value or a lost keystroke cannot silently break the attempt.
  fill_field 160 330 "$1"
  fill_field 160 400 "$2"
}
submit_form() {
  # Pressing Enter inside the password field triggers on_text_validate, which
  # is independent of the button position; fall back to tapping the button.
  local s0
  hide_keyboard
  s0=$(log_count "login_submit")
  tap 160 400 1
  "$ADB" shell input keyevent 66 >/dev/null 2>&1 || true
  for _ in 1 2 3; do
    [ "$(log_count 'login_submit')" -gt "$s0" ] && return 0
    sleep 2
  done
  for coords in "160 585" "160 575" "160 595" "160 600" "160 570"; do
    set -- $coords
    tap "$1" "$2" 2
    [ "$(log_count 'login_submit')" -gt "$s0" ] && return 0
  done
  return 1
}
submit_lens() {  # latest user_len pass_len server_len
  kivy_log | grep -a 'login_submit' | tail -n 1 \
    | sed -n 's/.*user_len=\([0-9]*\) pass_len=\([0-9]*\) server_len=\([0-9]*\).*/\1 \2 \3/p'
}
login_with() {  # user pass [screenshot-before-submit]
  local user="$1" pass="$2" shot_name="${3:-}" tries=0 lens got_u got_p
  local want_u=${#1} want_p=${#2}
  while [ "$tries" -lt 3 ]; do
    tries=$((tries+1))
    disable_imes
    fill_login "$user" "$pass"
    hide_keyboard
    [ -n "$shot_name" ] && shot "$shot_name.png"
    submit_form || fail "login form did not submit"
    sleep 2
    lens=$(submit_lens)
    got_u=${lens%% *}
    got_p=$(printf '%s' "$lens" | cut -d' ' -f2)
    [ -n "$got_u" ] || got_u=0
    [ -n "$got_p" ] || got_p=0
    if [ "$got_u" -eq "$want_u" ] && [ "$got_p" -eq "$want_p" ]; then
      echo "[journey] login input verified user_len=$got_u pass_len=$got_p (attempt $tries)"
      return 0
    fi
    echo "::notice title=journey::login input mismatch user_len=$got_u pass_len=$got_p want_user=$want_u want_pass=$want_p (attempt $tries)"
    sleep 2
  done
  return 1
}
pull_db() {
  "$ADB" shell cp "/data/user/0/$PKG/files/electrocalc.db" "/sdcard/$1.db" >/dev/null 2>&1 || true
  timeout 120 "$ADB" pull "/sdcard/$1.db" "$1.db" >/dev/null 2>&1 || true
  python3 db_state.py "$1.db" > "$1.json" 2>/dev/null || echo '{}' > "$1.json"
  echo "$1: $(cat "$1.json")" | tee -a db-timeline.txt
}
applog() { timeout 60 "$ADB" logcat -d -s python 2>/dev/null | grep -a "ElectroCalc:" || true; }
kivy_log() {
  timeout 90 "$ADB" shell "cat /data/user/0/$PKG/files/app/.kivy/logs/*.txt /data/user/0/$PKG/files/app/logs/*.txt 2>/dev/null" 2>/dev/null | tr -d '\r'
}
log_count() {
  local n
  n=$(kivy_log | grep -ac -- "$1")
  [ -n "$n" ] || n=0
  echo "$n"
}
applog_count() {
  local n
  n=$(applog | grep -ac -- "$1")
  [ -n "$n" ] || n=0
  echo "$n"
}
# grep -q can close the pipe early, which under pipefail reports the pipeline
# as failed even when the pattern matched; counting always drains the input.
log_has() { [ "$(log_count "$1")" -gt 0 ] || [ "$(applog_count "$1")" -gt 0 ]; }
wait_count_gt() {  # needle baseline tries [sleep]
  local needle="$1" base="$2" tries="${3:-10}" pause="${4:-2}" i
  for i in $(seq 1 "$tries"); do
    [ "$(log_count "$needle")" -gt "$base" ] && return 0
    sleep "$pause"
  done
  return 1
}
json_get() { python3 -c "import json,sys; print(json.load(open(sys.argv[1])).get(sys.argv[2],''))" "$1" "$2"; }

cat > db_state.py <<'PY'
import json, sqlite3, sys
connection = sqlite3.connect(sys.argv[1])
users = connection.execute("SELECT COUNT(*) FROM users").fetchone()[0]
row = connection.execute(
    "SELECT username, password_hash, role, is_superadmin, active, "
    "account_status, platform_android FROM users ORDER BY id LIMIT 1"
).fetchone()
flags = connection.execute(
    "SELECT COUNT(*) FROM app_settings WHERE key LIKE 'password_change_required:%'"
).fetchone()[0]
connection.close()
scheme = (
    "bcrypt" if row and str(row[1]).startswith(("$2a$", "$2b$", "$2y$"))
    else "other"
)
print(json.dumps({
    "users": users,
    "username": row[0] if row else "",
    "hash": row[1] if row else "",
    "role": row[2] if row else "",
    "superadmin": row[3] if row else None,
    "active": row[4] if row else None,
    "status": row[5] if row else "",
    "android": row[6] if row else None,
    "scheme": scheme,
    "flags": flags,
}, ensure_ascii=False))
PY

SMOKE_USER=smokeadmin
SMOKE_PASS=$(openssl rand -hex 8)
NEW_PASS=$(openssl rand -hex 9)
export SMOKE_PASS NEW_PASS
echo "::add-mask::$SMOKE_PASS"
echo "::add-mask::$NEW_PASS"

# ---- fresh installation ----
phase "fresh-install"
"$ADB" root >/dev/null 2>&1 || true
sleep 5
"$ADB" shell wm size 2>&1 | tee -a environment.txt || true
"$ADB" shell wm density 2>&1 | tee -a environment.txt || true
"$ADB" uninstall "$PKG" >/dev/null 2>&1 || true
sleep 2
timeout 300 "$ADB" install "$APK" 2>&1 | tee install.txt || fail "install failed"
"$ADB" shell svc wifi disable >/dev/null 2>&1 || true
"$ADB" shell svc data disable >/dev/null 2>&1 || true
FIRST_IME=""
for ime in $("$ADB" shell ime list -s 2>/dev/null | tr -d '\r'); do
  [ -n "$FIRST_IME" ] || FIRST_IME="$ime"
  "$ADB" shell ime disable "$ime" >/dev/null 2>&1 || true
done
{ echo "first_ime=$FIRST_IME"; "$ADB" shell ime list -s 2>/dev/null | tr -d '\r'; } | tee ime-state.txt
"$ADB" logcat -c >/dev/null 2>&1 || true
timeout 120 "$ADB" shell am start -n "$ACT" 2>&1 | tee launch.txt || true
STARTED=0
START_TS=$(date +%s)
TICK=0
RELAUNCHED=0
for _ in $(seq 1 300); do
  TICK=$((TICK+1))
  if [ "$(log_count 'app_start')" -gt 0 ]; then STARTED=1; break; fi
  if [ $((TICK % 8)) -eq 0 ]; then
    echo "$(date +%T) pid=$("$ADB" shell pidof "$PKG" 2>/dev/null | tr -d '\r') events=$(log_count 'ElectroCalc:')" >> startup-pid-timeline.txt
    if [ "$(log_count 'ElectroCalc:')" -eq 0 ] && [ "$(applog_count 'app_start')" -gt 0 ]; then
      STARTED=1
      break
    fi
  fi
  if [ $((TICK % 100)) -eq 0 ]; then
    echo "$(date +%T) kivy_lines=$(kivy_log | wc -l) python_lines=$(applog | wc -l)" >> startup-samples.txt
  fi
  if [ "$RELAUNCHED" = "0" ] && [ "$TICK" -ge 100 ] && [ "$(log_count 'build_begin')" -gt 0 ]; then
    echo "::notice title=startup::no app_start after 100 ticks; relaunching once"
    "$ADB" shell am force-stop "$PKG" >/dev/null 2>&1 || true
    sleep 3
    timeout 120 "$ADB" shell am start -n "$ACT" >> relaunch.txt 2>&1 || true
    RELAUNCHED=1
  fi
  sleep 6
done
echo "startup wait seconds: $(( $(date +%s) - START_TS ))" | tee startup-wait.txt
if [ "$STARTED" != "1" ]; then
  "$ADB" shell pidof "$PKG" | tr -d '\r' | tee startup-pid.txt || true
  timeout 60 "$ADB" logcat -d -b crash > startup-crash.txt 2>&1 || true
  timeout 60 "$ADB" logcat -d > startup-logcat.txt 2>&1 || true
  timeout 60 "$ADB" shell dumpsys activity activities 2>/dev/null | grep -aE "mResumedActivity|mCurrentFocus|electrocalc" > startup-activity.txt || true
  kivy_log > startup-kivy.log 2>/dev/null || true
  {
    echo "wait=$(cat startup-wait.txt) relaunched=$RELAUNCHED pid=$(tr '\n' ' ' < startup-pid.txt)"
    echo "klog_lines=$(wc -l < startup-kivy.log 2>/dev/null || echo 0) klog_events=$(grep -ac 'ElectroCalc:' startup-kivy.log || true) logcat_events=$(applog_count 'ElectroCalc:')"
    echo "klog app_start=$(grep -ac 'app_start' startup-kivy.log || true) build_begin=$(grep -ac 'build_begin' startup-kivy.log || true) module_import=$(grep -ac 'module_import' startup-kivy.log || true)"
    grep -a 'ElectroCalc:' startup-kivy.log | tail -n 3 | cut -c1-240
    grep -aE 'mResumedActivity|mFocusedWindow' startup-activity.txt | tail -n 2 | cut -c1-240
    tail -n 2 startup-crash.txt | cut -c1-240
  } | while IFS= read -r line; do
    echo "::error title=startup::${line}"
  done
  fail "app did not start"
fi
sleep 8
shot emulator-startup.png
"$ADB" shell pidof "$PKG" | tr -d '\r' | tee pid.txt || true
{
  echo "klog_app_start=$(log_count 'app_start') logcat_app_start=$(applog | grep -ac 'app_start') klog_lines=$(kivy_log | wc -l)"
} | tee log-source.txt
tail -n 1 log-source.txt | while IFS= read -r line; do echo "::notice title=logsource::${line}"; done

# ---- phase 0: fresh device database ----
phase "phase0-fresh-db"
pull_db db-initial
python3 - <<'PY' || fail "phase0: fresh database assertion failed"
import json
state = json.load(open("db-initial.json"))
assert state["users"] == 0, state
print("phase0 ok: fresh database has no accounts")
PY

# ---- phase 1: first-run admin setup ----
phase "phase1-bootstrap"
login_with "$SMOKE_USER" "$SMOKE_PASS" setup-filled \
  || fail "setup input could not be entered and verified"
SETUP_OK=0
for _ in $(seq 1 10); do
  sleep 3
  pull_db db-bootstrap
  if [ "$(json_get db-bootstrap.json users)" = "1" ]; then SETUP_OK=1; break; fi
done
sleep 2
shot change-dialog.png
"$ADB" shell pidof "$PKG" | tr -d '\r' | tee pid-after-setup.txt || true
[ "$SETUP_OK" = "1" ] || fail "admin creation did not save"
python3 - <<'PY' || fail "phase1: bootstrap database assertions failed"
import json
state = json.load(open("db-bootstrap.json"))
assert state["users"] == 1, state
assert state["username"], state
assert state["role"] == "admin", state
assert state["scheme"] == "bcrypt", state
assert state["superadmin"] == 1 and state["active"] == 1, state
assert state["status"] == "active" and state["android"] == 1, state
assert state["flags"] == 1, state
print("phase1 ok: one hashed superadmin with forced change flag")
PY
log_has "bootstrap=created" || fail "bootstrap event missing from log"

# ---- phase 2: forced password change ----
phase "phase2-forced-change"
sleep 2
disable_imes
hide_keyboard
tap 160 300 1
typ "$NEW_PASS"
hide_keyboard
tap 160 370 1
typ "$NEW_PASS"
hide_keyboard
shot change-form-filled.png
CHANGED=0
ATTEMPT=0
for coords in "240 460" "230 471" "200 462" "265 462" "250 470"; do
  set -- $coords
  ATTEMPT=$((ATTEMPT+1))
  hide_keyboard
  tap "$1" "$2" 2
  sleep 10
  pull_db db-changed
  shot "change-attempt-${ATTEMPT}.png"
  if [ "$(json_get db-changed.json flags)" = "0" ]; then CHANGED=1; break; fi
done
shot dashboard.png
"$ADB" shell pidof "$PKG" | tr -d '\r' | tee pid-after-change.txt || true
[ "$CHANGED" = "1" ] || fail "forced password change did not complete"
python3 - <<'PY' || fail "phase2: password change database assertions failed"
import json, os
state = json.load(open("db-changed.json"))
assert state["users"] == 1, state
assert state["scheme"] == "bcrypt", state
assert state["flags"] == 0, state
assert state["hash"] != os.environ["NEW_PASS"], "hash equals plaintext"
assert state["hash"] != os.environ["SMOKE_PASS"], "hash equals old plaintext"
print("phase2 ok: password replaced by new bcrypt hash, flag cleared")
PY
log_has "password_changed" || fail "password_changed event missing"
log_has "screen=dashboard" || fail "dashboard event missing"

# ---- phase 3: dashboard scroll ----
phase "phase3-dashboard-scroll"
"$ADB" shell input swipe 160 520 160 220 500 >/dev/null 2>&1 || true
sleep 2
shot dashboard-scrolled.png
"$ADB" shell input swipe 160 220 160 520 500 >/dev/null 2>&1 || true
sleep 2

# ---- phase 4: logout ----
phase "phase4-logout"
LOGGED_OUT=0
for coords in "284 52" "290 52" "280 52" "296 52" "240 52" "250 48" "288 40" "300 45" "236 56" "288 56" "304 52" "268 52"; do
  set -- $coords
  tap "$1" "$2" 3
  if log_has "action=logout"; then LOGGED_OUT=1; break; fi
done
shot logout-login.png
[ "$LOGGED_OUT" = "1" ] || fail "logout action not reached"

# ---- phase 5: old temporary password must be refused ----
phase "phase5-old-password"
DENIED0=$(log_count "login=denied")
OK0=$(log_count "login=ok")
login_with "$SMOKE_USER" "$SMOKE_PASS" login-old-filled \
  || fail "old-password input could not be entered and verified"
wait_count_gt "login=denied" "$DENIED0" 10 2 || fail "old password was not rejected"
[ "$(log_count 'login=ok')" -eq "$OK0" ] || fail "old password was accepted"
sleep 2
shot login-old-rejected.png
pull_db db-old-rejected
python3 - <<'PY' || fail "phase5: rejected-login database assertions failed"
import json
before = json.load(open("db-changed.json"))
after = json.load(open("db-old-rejected.json"))
assert after["users"] == 1, after
assert after["hash"] == before["hash"], "hash changed during rejected login"
print("phase5 ok: rejected login left the database untouched")
PY

# ---- phase 6: login with the new password ----
phase "phase6-relogin"
OK0=$(log_count "login=ok")
DASH0=$(log_count "screen=dashboard")
ATTEMPT=0
for _ in 1 2 3; do
  ATTEMPT=$((ATTEMPT+1))
  login_with "$SMOKE_USER" "$NEW_PASS" || fail "relogin input could not be entered and verified"
  wait_count_gt "login=ok" "$OK0" 10 2 && break
  sleep 2
  shot "relogin-attempt-${ATTEMPT}.png"
done
[ "$(log_count 'login=ok')" -gt "$OK0" ] || fail "relogin did not authenticate (attempts=${ATTEMPT})"
wait_count_gt "screen=dashboard" "$DASH0" 10 2 || fail "relogin did not reach dashboard"
sleep 3
shot dashboard-relogin.png
echo "dashboard events after relogin: $(log_count 'screen=dashboard')"

# ---- phase 7: restart and persistence ----
phase "phase7-restart"
"$ADB" shell am force-stop "$PKG" >/dev/null 2>&1 || true
for _ in $(seq 1 10); do
  [ -z "$("$ADB" shell pidof "$PKG" 2>/dev/null | tr -d '\r')" ] && break
  sleep 1
done
timeout 120 "$ADB" shell am start -n "$ACT" >> relaunch.txt 2>&1 || true
STARTS0=$(log_count "app_start")
RESTARTED=0
for _ in $(seq 1 150); do
  NEW_PID=$("$ADB" shell pidof "$PKG" 2>/dev/null | tr -d '\r')
  if [ -n "$NEW_PID" ] && [ "$(log_count 'app_start')" -gt "$STARTS0" ]; then
    RESTARTED=1
    break
  fi
  sleep 4
done
[ "$RESTARTED" = "1" ] || fail "app did not restart"
sleep 8
shot restart-login.png
OK0=$(log_count "login=ok")
DASH0=$(log_count "screen=dashboard")
ATTEMPT=0
for _ in 1 2 3; do
  ATTEMPT=$((ATTEMPT+1))
  login_with "$SMOKE_USER" "$NEW_PASS" || fail "restart login input could not be entered and verified"
  wait_count_gt "login=ok" "$OK0" 10 2 && break
  sleep 2
  shot "restart-login-attempt-${ATTEMPT}.png"
done
[ "$(log_count 'login=ok')" -gt "$OK0" ] || fail "login after restart did not authenticate"
wait_count_gt "screen=dashboard" "$DASH0" 10 2 || fail "login after restart did not reach dashboard"
sleep 3
shot dashboard-restart.png
"$ADB" shell pidof "$PKG" | tr -d '\r' | tee pid-final.txt || true
pull_db db-final
PID_BEFORE=$(tr -d '\r\n' < pid-after-change.txt || true)
PID_AFTER=$(tr -d '\r\n' < pid-final.txt || true)
echo "pids before=$PID_BEFORE after=$PID_AFTER"
[ -n "$PID_BEFORE" ] && [ -n "$PID_AFTER" ] && [ "$PID_BEFORE" != "$PID_AFTER" ] || fail "app did not restart"
echo "dashboard events after restart: $(log_count 'screen=dashboard')"
python3 - <<'PY' || fail "phase7: restart persistence assertions failed"
import json, os
changed = json.load(open("db-changed.json"))
final = json.load(open("db-final.json"))
assert final["users"] == 1, final
assert final["scheme"] == "bcrypt", final
assert final["flags"] == 0, final
assert final["hash"] == changed["hash"], "hash changed across restart"
for secret in (os.environ.get("SMOKE_PASS", ""), os.environ.get("NEW_PASS", "")):
    assert secret and secret not in final["hash"], "plaintext password stored"
print("phase7 ok: single admin persisted across restart, hashed, flag cleared")
PY

# ---- phase 8: ordered log evidence (Kivy's persistent log file) ----
phase "phase8-log-order"
kivy_log > app-log.txt
grep -ac "ElectroCalc:" app-log.txt | tee log-events.txt || true
python3 - <<'PY' || fail "phase8: ordered log assertions failed"
lines = open("app-log.txt", encoding="utf-8", errors="replace").read().splitlines()

def positions(needle):
    return [i for i, line in enumerate(lines) if needle in line]

def first(needle):
    found = positions(needle)
    assert found, f"missing log event: {needle}"
    return found[0]

bootstrap = first("bootstrap=created")
forced = first("password_change_required")
changed = first("password_changed")
dashboard_first = first("screen=dashboard")
logout = first("action=logout")
denied = first("login=denied")
login_ok = first("login=ok")
dashboard_last = positions("screen=dashboard")[-1]
starts = len(positions("app_start"))
submits = len(positions("login_submit"))

assert bootstrap < forced < changed, (bootstrap, forced, changed)
assert forced < dashboard_first < logout, (forced, dashboard_first, logout)
assert logout < denied < login_ok < dashboard_last, (logout, denied, login_ok, dashboard_last)
assert starts >= 2, f"expected two app starts, saw {starts}"
assert submits >= 3, f"expected at least three form submits, saw {submits}"
assert len(positions("screen=dashboard")) >= 3, "expected three dashboard entries"
print(f"phase8 ok: ordered events, {starts} app starts, {submits} submits, "
      f"{len(positions('screen=dashboard'))} dashboard entries")
PY

# ---- keyboard behaviour check ----
phase "keyboard-check"
tap 284 52 3
if [ -n "$FIRST_IME" ]; then
  "$ADB" shell ime enable "$FIRST_IME" >/dev/null 2>&1 || true
  "$ADB" shell ime set "$FIRST_IME" >/dev/null 2>&1 || true
fi
tap 160 330 3
shot login-keyboard.png
"$ADB" shell input keyevent 4 >/dev/null 2>&1 || true
sleep 2
shot login-keyboard-closed.png
"$ADB" shell pidof "$PKG" | tr -d '\r' > pid-keyboard.txt || true
test -s pid-keyboard.txt || fail "app died during keyboard interaction"
echo "keyboard check ok"

timeout 300 "$ADB" logcat -d > logcat.txt 2>&1 || true
timeout 120 "$ADB" logcat -d -b crash > logcat-crash.txt 2>&1 || true
ls -l dashboard.png dashboard-relogin.png dashboard-restart.png login-old-rejected.png 2>/dev/null || true
test -s pid.txt
test -s pid-final.txt
echo "[journey] PASSED"
