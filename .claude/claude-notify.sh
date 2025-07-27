#!/usr/bin/env bash
#
# claude-notify.sh
# A dispatcher for Claude’s Notification / Stop hooks.

set -eu

# If the first arg is “stop”, we know it’s a Stop event.
# Otherwise assume STDIN JSON is a Notification.
mode="$1"
payload="$(cat)"   # read entire JSON from STDIN

if [[ "$mode" == "stop" ]]; then
  # simple “done” with check + rocket
  msg="done! ✅🚀"
else
  # parse JSON to figure out sub‑type
  # you’ll need `jq` installed
  event=$(jq -r '.event' <<<"$payload")
  case "$event" in

    task.permission_required|permission_required)
      reason=$(jq -r '.payload.reason // "no reason given"' <<<"$payload")
      msg="🔒 Permission needed: $reason"
      ;;

    task.proceed_required|proceed)
      detail=$(jq -r '.payload.detail // "confirm to continue"' <<<"$payload")
      msg="⏭️ Proceed requested: $detail"
      ;;

    *)
      # fallback: just dump the user‑facing message
      text=$(jq -r '.payload.message // empty' <<<"$payload")
      [[ -n "$text" ]] && msg="💬 $text" || msg="💬 (notification)"
      ;;
  esac
fi

# finally, post to ntfy.sh
curl -s -d "$msg" https://ntfy.sh/claude-alert >/dev/null
