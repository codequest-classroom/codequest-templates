import os
import json
import requests
from datetime import datetime
import base64

def check_mission():
    """Main grading function"""
    
    print("🤖 CodeQuest AI Reviewer Starting...")
    
    # Load all necessary files
    with open('mission.json', 'r') as f:
        mission = json.load(f)
    
    with open('rubric.json', 'r') as f:
        rubric = json.load(f)
    
    with open('identity.json', 'r') as f:
        identity = json.load(f)
    
    # Check if already completed
    if mission['id'] in [m['id'] for m in identity.get('completedMissions', [])]:
        print("✅ Mission already completed!")
        return True
    
    # Check if submissions exist
    html_path = 'submissions/index.html'
    css_path = 'submissions/style.css'
    
    html_exists = os.path.exists(html_path)
    css_exists = os.path.exists(css_path)
    
    results = []
    all_pass = True
    
    # Basic file checks
    if not html_exists:
        results.append({
            "req": "HTML file exists",
            "pass": False,
            "feedback": "Missing submissions/index.html file"
        })
        all_pass = False
    else:
        with open(html_path, 'r') as f:
            html_content = f.read()
        
        # Check for basic HTML structure
        checks = [
            ("DOCTYPE declaration", "<!DOCTYPE html>" in html_content),
            ("HTML tags", "<html" in html_content and "</html>" in html_content),
            ("Head section", "<head" in html_content and "</head>" in html_content),
            ("Body section", "<body" in html_content and "</body>" in html_content),
        ]
        
        for check_name, passed in checks:
            results.append({
                "req": check_name,
                "pass": passed,
                "feedback": "Good!" if passed else f"Missing {check_name}"
            })
            if not passed:
                all_pass = False
    
    if not css_exists:
        results.append({
            "req": "CSS file exists",
            "pass": False,
            "feedback": "Missing submissions/style.css file"
        })
        all_pass = False
    
    # Generate feedback.md
    generate_feedback(mission, rubric, identity, results, all_pass)
    
    # If passed, update identity and master record
    if all_pass:
        update_student_progress(identity, mission)
    
    return all_pass

def generate_feedback(mission, rubric, identity, results, passed):
    """Create feedback.md file"""
    
    username = identity.get('username', 'student')
    
    with open('feedback.md', 'w') as f:
        f.write(f"# 🤖 CodeQuest AI Review\n\n")
        
        if passed:
            f.write(f"## ✅ MISSION PASSED! 🎉\n\n")
            f.write(f"Great job, {identity.get('name', 'Coder')}!\n\n")
            f.write(f"### +{mission['points']} XP EARNED\n")
            if mission.get('badge'):
                f.write(f"### 🏆 Badge Unlocked: {mission['badge']}\n")
        else:
            f.write(f"## ❌ NOT QUITE YET\n\n")
            f.write(f"Keep trying, {identity.get('name', 'Coder')}! Here's what needs work:\n\n")
        
        f.write(f"### Results:\n")
        for r in results:
            icon = "✅" if r['pass'] else "❌"
            f.write(f"{icon} **{r['req']}**: {r['feedback']}\n")
        
        if not passed:
            f.write(f"\n💡 Fix the ❌ items above, save your files, and push again!\n")
        
        # Always link to their personal site
        f.write(f"\n---\n")
        f.write(f"## 🌐 View Your Progress:\n")
        f.write(f"👉 **https://{username}.github.io**\n")
        f.write(f"\n*Click the 🔓 button on your site to start your next mission!*\n")
    
    print("✅ feedback.md generated")

def update_student_progress(identity, mission):
    """Update identity.json and sync with master repo"""
    
    # Update local identity
    if 'completedMissions' not in identity:
        identity['completedMissions'] = []
    
    identity['completedMissions'].append({
        'id': mission['id'],
        'points': mission['points'],
        'completedAt': datetime.now().isoformat()
    })
    
    identity['xp'] = identity.get('xp', 0) + mission['points']
    
    if mission.get('badge') and mission['badge'] not in identity.get('badges', []):
        if 'badges' not in identity:
            identity['badges'] = []
        identity['badges'].append(mission['badge'])
    
    # Save local identity
    with open('identity.json', 'w') as f:
        json.dump(identity, f, indent=2)
    
    print("✅ Local identity updated")
    
    # Here you would also update the master repo via GitHub API
    # This requires GH_TOKEN environment variable
    update_master_record(identity)

def update_master_record(identity):
    """Update the student's record in master repo"""
    
    token = os.environ.get('GH_TOKEN')
    if not token:
        print("⚠️ No GH_TOKEN found - skipping master update")
        return
    
    username = identity.get('username')
    if not username:
        print("⚠️ No username in identity")
        return
    
    # GitHub API call to update master repo
    # This is simplified - you'd need the full implementation
    print(f"📡 Would update master record for {username}")

if __name__ == "__main__":
    passed = check_mission()
    exit(0 if passed else 1)
