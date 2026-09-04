import subprocess

# Get some sample candidates
cmd = [
    "python3", "-m", "yt_dlp",
    "--cookies-from-browser", "chrome",
    "--flat-playlist", 
    "--print", "%(id)s|%(title)s|%(channel)s|%(duration)s|%(view_count)s",
    "ytsearch3:stand-up comedy full special",
    "--no-download"
]
result = subprocess.run(cmd, capture_output=True, text=True)

candidates = []
if result.returncode == 0:
    for line in result.stdout.strip().split('\n'):
        if '|' in line:
            parts = line.split('|')
            if len(parts) >= 5:
                video_id, title, channel, duration, views = parts[:5]
                try:
                    candidates.append({
                        "video_id": video_id.strip(),
                        "title": title.strip(),
                        "channel": channel.strip(),
                        "language": "en",
                        "duration": int(duration) if duration.isdigit() else 0,
                        "view_count": int(views) if views.isdigit() else 0,
                    })
                except:
                    continue

print(f"Generated {len(candidates)} candidates")

# Test filter logic
SUPPORTED_LANGUAGES = {"en", "zh", "hi"}
filtered = []
rejects = []
for c in candidates:
    # Duration filter (30s - 30min)
    duration_ok = c.get('duration', 0) >= 30 and c.get('duration', 0) <= 1800
    # Minimum views for quality (1000 views minimum)
    views_ok = c.get('view_count', 0) >= 1000
    # Language must be supported
    lang_ok = c.get('language') in SUPPORTED_LANGUAGES
    
    if duration_ok and views_ok and lang_ok:
        filtered.append(c)
    else:
        rejects.append({
            'candidate': c,
            'duration_ok': duration_ok,
            'views_ok': views_ok,
            'lang_ok': lang_ok
        })

print(f"Filtered to {len(filtered)} candidates")
print(f"Rejected {len(rejects)} candidates")

# Show first 3 rejects
for i, r in enumerate(rejects[:3]):
    print(f"Reject {i+1}: {r['candidate']['video_id']}")
    print(f"  Duration: {r['duration_ok']} (duration={r['candidate']['duration']}s)")
    print(f"  Views: {r['views_ok']} (views={r['candidate']['view_count']})")
    print(f"  Language: {r['lang_ok']} (lang={r['candidate']['language']})")
    print()

if filtered:
    print("Sample filtered candidates:")
    for i, c in enumerate(filtered[:3]):
        print(f"  {c['video_id']}: {c['duration']}s, {c['view_count']} views")
