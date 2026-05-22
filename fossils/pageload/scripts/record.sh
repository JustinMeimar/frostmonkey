#!/usr/bin/env bash
set -euo pipefail

FIREFOX="/home/justin/spidermonkey/firefox"
DIR="$(cd "$(dirname "$0")/.." && pwd)"
RECORDINGS="$DIR/recordings"
mkdir -p "$RECORDINGS"
PORT=8081

SITES=(
    "reddit|https://www.reddit.com"
    "wikipedia|https://en.wikipedia.org/wiki/Barack_Obama"
    "youtube|https://www.youtube.com"
    "amazon|https://www.amazon.com/s?k=laptop"
    "imdb|https://www.imdb.com/title/tt0084967/"
    "bing|https://www.bing.com/search?q=javascript"
    "fandom|https://marvel.fandom.com/wiki/Black_Panther"
    "stackoverflow|https://stackoverflow.com/questions/927358/how-do-i-undo-the-most-recent-commits-in-git"
)

for entry in "${SITES[@]}"; do
    IFS='|' read -r name url <<< "$entry"
    FLOW="$RECORDINGS/$name.flow"
    echo "==> Recording $name ($url)"

    mitmdump -w "$FLOW" -p "$PORT" -q &
    MPID=$!
    sleep 2

    cd "$FIREFOX" && MOZ_DISABLE_CONTENT_SANDBOX=1 \
        MOZCONFIG=../mozconfigs/browser-release.mozconfig \
        ./mach browsertime --headless -n 1 -b firefox \
        --firefox.binaryPath "$FIREFOX/build-browser-release/dist/bin/firefox" \
        --proxy.http "localhost:$PORT" \
        --proxy.https "localhost:$PORT" \
        --firefox.acceptInsecureCerts \
        "$url" 2>&1 | tail -5

    kill "$MPID" 2>/dev/null; wait "$MPID" 2>/dev/null || true
    echo "    Saved $FLOW ($(du -h "$FLOW" | cut -f1))"
done

echo "Done. Recordings in $RECORDINGS"
