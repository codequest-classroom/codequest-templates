import os
import json
import requests
from datetime import datetime
import base64
import subprocess

def check_mission():
    """Main grading function"""
    
    print("🤖 CodeQuest AI Reviewer Starting...")
    print("=" * 50)
    
    # Load all necessary files
    try:
        with open('mission.json', 'r') as f:
            mission = json.load(f)
        print(f"✅ Loaded mission: {mission.get('title', 'Unknown')}")
    except Exception as e:
        print(f"❌ Failed to load mission.json: {e}")
        return False
    
    try:
        with open('rubric.json', 'r') as f:
            rubric = json.load(f)
        print(f"✅ Loaded rubric with {len(rubric.get('checks', []))} checks")
    except Exception as e:
        print(f"❌ Failed to load rubric.json: {e}")
        return False
    
    try:
        with open('identity.json', 'r') as f:
            identity = json.load(f)
        print(f"✅ Loaded identity for: {identity.get('name', 'Unknown')}")
    except Exception as e:
        print(f"❌ Failed to load identity.json: {e}")
        return False
    
    # Check if already completed
    completed_ids = [m['id'] for m in identity.get('completedMissions', [])]
    if mission['id'] in completed_ids:
        print("✅ Mission already completed! Skipping...")
        return True
    
    print("\n🔍 Running checks...")
    print("-" * 50)
    
    # Run checks from rubric
    results = []
    all_pass = True
    total_points = 0
    
    for check in rubric.get('checks', []):
        check_name = check.get('name', 'Unknown check')
        test_command = check.get('test', '')
        feedback = check.get('feedback', 'No feedback provided')
        
        print(f"  Checking: {check_name}...")
        
        # Run the test command
        passed = False
        if test_command:
            try:
                # For simple file existence checks
                if test_command.startswith('test -f'):
                    file_path = test_command.replace('test -f', '').strip()
                    passed = os.path.exists(file_path)
                # For grep commands
                elif 'grep' in test_command:
                    result = subprocess.run(
                        test_command,
                        shell=True,
                        capture_output=True,
                        text=True
                    )
                    passed = result.returncode == 0
                # For other commands
                else:
                    result = subprocess.run(
                        test_command,
                        shell=True,
                        capture_output=True,
                        text=True
                    )
                    passed = result.returncode == 0
            except Exception as e:
                print(f"    ⚠️ Test error: {e}")
                passed = False
        
        if passed:
            print(f"    ✅ PASSED")
            results.append({
                "req": check_name,
                "pass": True,
                "feedback": "Good job! ✓"
            })
            total_points += 1
        else:
            print(f"    ❌ FAILED")
            results.append({
                "req": check_name,
                "pass": False,
                "feedback": feedback
            })
            all_pass = False
    
    print("-" * 50)
    print(f"\n📊 Results: {sum(1 for r in results if r['pass'])}/{len(results)} passed")
    
    # Determine if passed based on passing score
    passing_score = rubric.get('passingScore', len(results))
    points_earned = sum(1 for r in results if r['pass'])
    passed = points_earned >= passing_score
    
    # Generate feedback.md
    generate_feedback(mission, identity, results, passed, points_earned)
    
    # If passed, update identity and trigger next steps
    if passed:
        print(f"\n🎉 MISSION PASSED! Awarding {mission.get('points', 0)} XP")
        update_student_progress(identity, mission, results)
    else:
        print(f"\n❌ Mission not passed yet. Keep trying!")
    
    return passed

def generate_feedback(mission, identity, results, passed, points_earned):
    """Create feedback.md file"""
    
    username = identity.get('username', 'student')
    student_name = identity.get('name', 'Coder')
    total_checks = len(results)
    
    with open('feedback.md', 'w') as f:
        f.write(f"# 🤖 CodeQuest AI Review\n\n")
        
        if passed:
            f.write(f"## ✅ MISSION PASSED! 🎉\n\n")
            f.write(f"Great job, {student_name}!\n\n")
            f.write(f"### ✨ +{mission.get('points', 0)} XP EARNED\n")
            if mission.get('badge'):
                f.write(f"### 🏆 Badge Unlocked: {mission['badge']}\n")
            f.write(f"\nYou passed {points_earned}/{total_checks} checks!\n")
        else:
            f.write(f"## ❌ NOT QUITE YET\n\n")
            f.write(f"Keep trying, {student_name}! Here's what needs work:\n\n")
            f.write(f"### 📊 Score: {points_earned}/{total_checks}\n\n")
        
        f.write(f"\n### 📋 Detailed Results:\n")
        for r in results:
            icon = "✅" if r['pass'] else "❌"
            f.write(f"{icon} **{r['req']}**: {r['feedback']}\n")
        
        if not passed:
            f.write(f"\n💡 Fix the ❌ items above, save your files, and push again!\n")
        
        # Always link to their personal site
        f.write(f"\n---\n")
        f.write(f"## 🌐 View Your Progress:\n")
        f.write(f"👉 **https://{username}.github.io**\n")
        f.write(f"\n*Click the glowing circles on your site to start your next mission!*\n")
    
    print("✅ feedback.md generated")

def update_student_progress(identity, mission, results):
    """Update identity.json and sync with master repo"""
    
    # Get current timestamp
    now = datetime.now().isoformat()
    
    # Initialize fields if they don't exist
    if 'completedMissions' not in identity:
        identity['completedMissions'] = []
    if 'xp' not in identity:
        identity['xp'] = 0
    if 'badges' not in identity:
        identity['badges'] = []
    
    # Add completed mission
    identity['completedMissions'].append({
        'id': mission['id'],
        'points': mission['points'],
        'completedAt': now,
        'results': results
    })
    
    # Add XP
    identity['xp'] += mission['points']
    
    # Add badge if exists and not already earned
    if mission.get('badge') and mission['badge'] not in identity['badges']:
        identity['badges'].append(mission['badge'])
        print(f"🏆 Badge earned: {mission['badge']}")
    
    # Calculate next mission
    next_mission = determine_next_mission(identity, mission)
    if next_mission:
        identity['currentMission'] = next_mission
        print(f"🎯 Next mission: {next_mission}")
        
        # Trigger creation of next mission repo
        create_next_mission_repo(identity['username'], next_mission)
    
    # Save local identity
    with open('identity.json', 'w') as f:
        json.dump(identity, f, indent=2)
    
    print("✅ Local identity updated")
    
    # Update master repo
    update_master_record(identity)
    
    print(f"📊 Total XP now: {identity['xp']}")
    print(f"🏅 Badges: {', '.join(identity['badges'])}")

def determine_next_mission(identity, completed_mission):
    """Determine which mission should be next"""
    
    # This would normally check the path/level structure
    # For demo, just increment the mission number
    mission_id = completed_mission['id']
    
    # Simple progression for demo
    progression = {
        'html-1-1': 'html-1-2',
        'html-1-2': 'html-1-3',
        'html-1-3': 'css-2-1',
        'css-2-1': 'css-2-2',
        'css-2-2': 'css-2-3',
        'css-2-3': None
    }
    
    return progression.get(mission_id)

def create_next_mission_repo(username, next_mission):
    """Call the create-student-repo script to make next mission"""
    
    print(f"📦 Creating next mission repo: {username}-{next_mission}")
    
    # This would call your create-student-repo.py script
    # For now, just print
    print(f"🔧 Would create: https://github.com/codequest-classroom/{username}-{next_mission}")

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
    
    # This would use GitHub API to update master repo
    print(f"📡 Syncing with master repo for {username}")
    
    # For demo, just print what would happen
    print(f"   Would update: students/{username}.json")
    print(f"   New XP: {identity['xp']}")
    print(f"   New badges: {identity['badges']}")

if __name__ == "__main__":
    passed = check_mission()
    exit(0 if passed else 1)
