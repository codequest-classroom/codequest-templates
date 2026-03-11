import os, json, requests, base64, subprocess
from datetime import datetime

def check_mission():
    """Grades the work, updates XP, and triggers all 'nextInLevel' missions."""
    print("🚀 CodeQuest Reviewer: checking submissions/index.html...")
    
    # 1. Load context
    with open('mission.json', 'r') as f: mission = json.load(f)
    with open('rubric.json', 'r') as f: rubric = json.load(f)
    with open('identity.json', 'r') as f: identity = json.load(f)

    # 2. Run the tests from the rubric
    results = []
    points_earned = 0
    for check in rubric.get('checks', []):
        # We run the test command (e.g., grep)
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
            
            # Sync to the Master Repo (This updates the skill tree website)
            sync_to_master(identity)
            
            # 4. Trigger ALL next missions (Points-based branching)
            next_missions = mission.get('nextInLevel', [])
            for next_id in next_missions:
                trigger_next_gen(identity['username'], next_id)
                print(f"🔗 Triggering next mission: {next_id}")

    # 5. Write feedback for the student to read in GitHub
    write_feedback_file(is_passed, points_earned, results, identity)
    return is_passed

def sync_to_master(identity):
    """Updates the master student record so script.js sees the new points."""
    token = os.environ.get('GH_TOKEN')
    user = identity['username']
    url = f"https://api.github.com/repos/codequest-classroom/codequest-master/contents/students/{user}.json"
    headers = {"Authorization": f"token {token}"}

    # Format the JSON exactly how script.js expects it
    master_json = {
        "student": {"name": identity['name'], "username": user},
        "progress": {
            "xp": identity['xp'],
            "completedMissions": identity['completedMissions'],
            "badges": identity.get('badges', [])
        }
    }

    # Get SHA for the update
    res = requests.get(url, headers=headers)
    sha = res.json().get('sha') if res.status_code == 200 else None
    
    requests.put(url, headers=headers, json={
        "message": f"🏆 {user} passed {identity.get('currentMission', 'mission')}",
        "content": base64.b64encode(json.dumps(master_json, indent=2).encode()).decode(),
        "sha": sha
    })

def trigger_next_gen(user, mission_id):
    """Calls the master repo workflow to build the next challenge."""
    token = os.environ.get('GH_TOKEN')
    url = "https://api.github.com/repos/codequest-classroom/codequest-master/actions/workflows/invite-student.yml/dispatches"
    requests.post(url, headers={"Authorization": f"token {token}"}, 
                  json={"ref": "main", "inputs": {"username": user, "mission_id": mission_id}})

def write_feedback_file(passed, score, results, identity):
    with open('feedback.md', 'w') as f:
        status = "🎉 MISSION PASSED!" if passed else "⚠️ MISSION INCOMPLETE"
        f.write(f"# {status}\n\n")
        f.write(f"### Points: {score} | Total XP: {identity['xp']}\n\n")
        f.write("### Reviewer Results:\n")
        for r in results:
            f.write(f"- {r['feedback']} **{r['name']}**\n")
        f.write(f"\n[View your Progress Tree](https://{identity['username']}.github.io)")

if __name__ == "__main__":
    check_mission()
