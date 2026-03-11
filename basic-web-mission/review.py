import os
import json
import requests
import base64
import subprocess
from datetime import datetime

def check_mission():
    """Main grading and unlocking engine"""
    print("🤖 CodeQuest AI Reviewer Starting...")
    
    # 1. Load Local Files
    try:
        with open('mission.json', 'r') as f: mission = json.load(f)
        with open('rubric.json', 'r') as f: rubric = json.load(f)
        with open('identity.json', 'r') as f: identity = json.load(f)
    except Exception as e:
        print(f"❌ Initialization Error: {e}")
        return False

    # 2. Run Rubric Checks
    results = []
    points_earned = 0
    for check in rubric.get('checks', []):
        print(f"🔎 Checking: {check['name']}...")
        # Runs the shell command (e.g., 'grep' or 'test -f')
        process = subprocess.run(check['test'], shell=True, capture_output=True, text=True)
        passed = (process.returncode == 0)
        
        results.append({
            "req": check['name'],
            "pass": passed,
            "feedback": "✅ Done!" if passed else f"❌ {check['feedback']}"
        })
        if passed: points_earned += 1

    # 3. Determine if Passed
    passing_score = rubric.get('passingScore', 1)
    is_passed = points_earned >= passing_score

    # 4. Generate feedback.md (What the student sees in GitHub)
    generate_feedback_file(mission, identity, results, is_passed, points_earned)

    # 5. If Passed: Update Master Repo & Trigger Next Mission
    if is_passed:
        # Prevent double-grading if they push again
        already_done = any(m['id'] == mission['id'] for m in identity.get('completedMissions', []))
        if not already_done:
            update_student_data(identity, mission)
            
            # Look at mission.json to see what's next
            next_mission_id = mission.get('nextInLevel', [None])[0]
            if next_mission_id:
                trigger_next_repo_creation(identity['username'], next_mission_id)
    
    return is_passed

def update_student_data(identity, mission):
    """Updates the Central Master Repo so the website reflects the win"""
    token = os.environ.get('GH_TOKEN')
    username = identity['username']
    org = "codequest-classroom"
    
    # Update local identity first
    identity['xp'] += mission.get('points', 0)
    identity['completedMissions'].append({
        "id": mission['id'],
        "points": mission.get('points', 0),
        "completedAt": datetime.now().isoformat()
    })

    # Prepare JSON for the Website (matches your script.js structure)
    master_json = {
        "student": {"name": identity['name'], "username": username},
        "progress": {
            "xp": identity['xp'],
            "completedMissions": identity['completedMissions'],
            "badges": identity.get('badges', [])
        }
    }

    # API call to update codequest-master/students/username.json
    url = f"https://api.github.com/repos/{org}/codequest-master/contents/students/{username}.json"
    headers = {"Authorization": f"token {token}"}
    
    # Get SHA to overwrite
    res = requests.get(url, headers=headers)
    sha = res.json().get('sha') if res.status_code == 200 else None

    payload = {
        "message": f"🏆 {username} completed {mission['id']}",
        "content": base64.b64encode(json.dumps(master_json, indent=2).encode()).decode(),
        "sha": sha
    }
    
    requests.put(url, headers=headers, json=payload)
    print(f"📡 Master Record Updated for {username}")

def trigger_next_repo_creation(username, next_mission_id):
    """Triggers the GitHub Action in the Master repo to build the next repo"""
    token = os.environ.get('GH_TOKEN')
    url = "https://api.github.com/repos/codequest-classroom/codequest-master/actions/workflows/invite-student.yml/dispatches"
    
    payload = {
        "ref": "main",
        "inputs": {
            "username": username,
            "mission_id": next_mission_id
        }
    }
    requests.post(url, headers={"Authorization": f"token {token}"}, json=payload)
    print(f"📦 Next mission triggered: {next_mission_id}")

def generate_feedback_file(mission, identity, results, is_passed, score):
    with open('feedback.md', 'w') as f:
        status = "✅ MISSION PASSED!" if is_passed else "❌ MISSION INCOMPLETE"
        f.write(f"# {status}\n\n")
        f.write(f"### Score: {score}/{len(results)}\n\n")
        for r in results:
            f.write(f"- {r['feedback']}\n")
        f.write(f"\n---\n**Check your progress here:** https://{identity['username']}.github.io")

if __name__ == "__main__":
    check_mission()
