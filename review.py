import os, json, requests, base64, subprocess
from datetime import datetime

def check_mission():
    """Grades the work, updates XP, and triggers all 'nextInLevel' missions."""
    print("🚀 CodeQuest Reviewer: checking submissions/index.html...")
    
    # 1. Load context (utf-8-sig handles BOM characters if present)
    with open('mission.json', 'r', encoding='utf-8-sig') as f: mission = json.load(f)
    with open('rubric.json', 'r', encoding='utf-8-sig') as f: rubric = json.load(f)
    with open('identity.json', 'r', encoding='utf-8-sig') as f: identity = json.load(f)

    # 2. Run the tests from the rubric
    results = []
    points_earned = 0
    for check in rubric.get('checks', []):
        process = subprocess.run(check['test'], shell=True, capture_output=True)
        passed = (process.returncode == 0)
        
        results.append({
            "name": check['name'],
            "pass": passed,
            "feedback": "✅" if passed else f"❌ {check['feedback']}"
        })
        if passed: points_earned += 1

    # 3. Determine if the student passed based on rubric passingScore
    is_passed = points_earned >= rubric.get('passingScore', 1)
    
    if is_passed:
        # Check if mission was already completed to prevent XP farming
        already_completed = any(m['id'] == mission['id'] for m in identity.get('completedMissions', []))
        
        if not already_completed:
            # Update local identity
            identity['xp'] = identity.get('xp', 0) + mission.get('points', 0)
            if 'completedMissions' not in identity: identity['completedMissions'] = []
            
            identity['completedMissions'].append({
                "id": mission['id'],
                "at": datetime.now().isoformat()
            })
            
            old_xp = identity['xp'] - mission.get('points', 0)

            # Sync to the Master Repo (This updates the skill tree website)
            sync_to_master(identity)

            # 4. XP-threshold unlocking: trigger all missions in newly-unlocked levels
            unlock_new_levels(identity, old_xp, identity['xp'])
            # Re-sync so unlockedMissions is written to progress.json
            sync_to_master(identity)

    # 5. Write feedback for the student to read in GitHub
    write_feedback_file(is_passed, points_earned, results, identity)
    return is_passed

def sync_to_master(identity):
    """Updates the master student record so script.js sees the new points."""
    token = os.environ.get('GH_TOKEN')
    user = identity['username']
    url = f"https://api.github.com/repos/codequest-classroom/codequest-master/contents/students/{user}.json"
    headers = {"Authorization": f"token {token}"}

    # FIX: GET existing master record first to preserve all fields (id, joined, status etc.)
    res = requests.get(url, headers=headers)
    sha = None
    existing = {}

    if res.status_code == 200:
        sha = res.json().get('sha')
        try:
            existing = json.loads(base64.b64decode(res.json()['content']))
        except Exception as e:
            print(f"⚠️ Could not decode existing master record: {e}")

    # Preserve existing student fields, only update progress
    existing.setdefault('student', {})
    existing.setdefault('progress', {})
    existing['student']['name'] = identity['name']
    existing['student']['username'] = user
    existing['progress']['xp'] = identity['xp']
    existing['progress']['completedMissions'] = identity['completedMissions']
    existing['progress']['unlockedMissions'] = identity.get('unlockedMissions', [])
    existing['progress']['badges'] = identity.get('badges', [])
    existing['progress']['currentMission'] = identity.get('currentMission', '')

    put_payload = {
        "message": f"🏆 {user} passed {identity.get('currentMission', 'mission')}",
        "content": base64.b64encode(json.dumps(existing, indent=2).encode()).decode(),
    }
    if sha:
        put_payload["sha"] = sha

    result = requests.put(url, headers=headers, json=put_payload)
    if result.status_code in [200, 201]:
        print(f"✅ Master record updated for {user}")
    else:
        print(f"❌ Failed to update master record: {result.status_code} - {result.text}")

    # Also push progress to the public portfolio repo so the site can read it
    sync_to_portfolio(identity, existing, headers)

def sync_to_portfolio(identity, master_data, headers):
    """Pushes progress.json to the public codequest-classroom/{username} repo so the site can read it."""
    user = identity['username']
    url = f"https://api.github.com/repos/codequest-classroom/{user}/contents/progress.json"

    existing = requests.get(url, headers=headers)
    put_payload = {
        "message": f"🏆 Progress update",
        "content": base64.b64encode(json.dumps(master_data, indent=2).encode()).decode()
    }
    if existing.status_code == 200:
        put_payload["sha"] = existing.json().get("sha")

    result = requests.put(url, headers=headers, json=put_payload)
    if result.status_code in [200, 201]:
        print(f"✅ Portfolio progress updated for {user}")
    else:
        print(f"❌ Failed to update portfolio progress: {result.status_code} - {result.text}")

def unlock_new_levels(identity, old_xp, new_xp):
    """Fetch web-dev.json and trigger all missions in any level newly crossed by XP."""
    token = os.environ.get('GH_TOKEN')
    headers = {"Authorization": f"token {token}"}
    path_url = "https://api.github.com/repos/codequest-classroom/codequest-master/contents/paths/web-dev.json"
    res = requests.get(path_url, headers=headers)
    if res.status_code != 200:
        print(f"⚠️ Could not fetch path config: {res.status_code}")
        return

    path_config = json.loads(base64.b64decode(res.json()['content']))
    if 'unlockedMissions' not in identity:
        identity['unlockedMissions'] = []

    for level in path_config.get('levels', []):
        threshold = level.get('pointsToUnlock', 0)
        # Trigger missions only when XP just crossed this level's threshold
        if old_xp < threshold <= new_xp:
            print(f"🔓 Level '{level['name']}' unlocked at {new_xp} XP!")
            for m in level.get('missions', []):
                mission_id = m['id'] if isinstance(m, dict) else m
                if mission_id not in identity['unlockedMissions']:
                    trigger_next_gen(identity, mission_id)
                    identity['unlockedMissions'].append(mission_id)
                    print(f"   ➕ Triggered: {mission_id}")

def trigger_next_gen(identity, mission_id):
    """Calls the master repo workflow to build the next challenge."""
    token = os.environ.get('GH_TOKEN')
    url = "https://api.github.com/repos/codequest-classroom/codequest-master/actions/workflows/invite-student.yml/dispatches"
    
    # FIX: input names now match exactly what invite-student.yml expects
    payload = {
        "ref": "main",
        "inputs": {
            "student_username": identity['username'],
            "student_name": identity['name'],
            "first_mission": mission_id
        }
    }
    
    result = requests.post(url, headers={"Authorization": f"token {token}"}, json=payload)
    if result.status_code == 204:
        print(f"✅ Next mission triggered: {mission_id}")
    else:
        print(f"❌ Failed to trigger next mission: {result.status_code} - {result.text}")

def write_feedback_file(passed, score, results, identity):
    with open('feedback.md', 'w') as f:
        status = "🎉 MISSION PASSED!" if passed else "⚠️ MISSION INCOMPLETE"
        f.write(f"# {status}\n\n")
        f.write(f"### Points: {score} | Total XP: {identity['xp']}\n\n")
        f.write("### Reviewer Results:\n")
        for r in results:
            f.write(f"- {r['feedback']} **{r['name']}**\n")
        f.write(f"\n[View your Progress Tree](https://codequest-classroom.github.io/{identity['username']})")

if __name__ == "__main__":
    check_mission()