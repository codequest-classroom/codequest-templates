// Detects the username based on the GitHub Pages URL (e.g., "mishael.github.io")
const username = window.location.hostname.split('.')[0];

// Your Mission Map
const missionTree = {
    "web-level-1": {
        name: "HTML Basics",
        description: "🏗️ Build your first web pages!",
        emoji: "📝",
        missions: [
            { id: "html-1-1", name: "Structure", repo: `${username}-html-1-1`, points: 5, number: 1 },
            { id: "html-1-2", name: "Text", repo: `${username}-html-1-2`, points: 5, number: 2 },
            { id: "html-1-3", name: "Links & Images", repo: `${username}-html-1-3`, points: 5, number: 3 }
        ],
        minToComplete: 2,
        unlocks: ["web-level-2"]
    },
    "web-level-2": {
        name: "CSS Basics",
        description: "🎨 Make things beautiful!",
        emoji: "✨",
        missions: [
            { id: "css-2-1", name: "Selectors", repo: `${username}-css-2-1`, points: 8, number: 4 },
            { id: "css-2-2", name: "Box Model", repo: `${username}-css-2-2`, points: 8, number: 5 },
            { id: "css-2-3", name: "Colors", repo: `${username}-css-2-3`, points: 8, number: 6 }
        ],
        minToComplete: 2,
        unlocks: []
    }
};

async function loadStudentProgress() {
    try {
        // Fetch progress from the master repo (updated by review.py)
        const response = await fetch(
            `https://raw.githubusercontent.com/codequest-classroom/codequest-master/main/students/${username}.json`
        );
        
        if (!response.ok) throw new Error('Student data not found');
        
        const data = await response.json();
        const student = data.student;
        const progress = data.progress;

        // Update UI Header
        document.getElementById('student-name').textContent = `${student.name}'s Coding Quest 🚀`;
        document.getElementById('xp').textContent = progress.xp || 0;
        document.getElementById('badges').textContent = progress.badges ? progress.badges.length : 0;

        // Logic: Determine which levels are unlocked
        let unlockedLevels = ["web-level-1"];
        
        // Loop through levels to see if previous ones were completed
        for (let [levelId, level] of Object.entries(missionTree)) {
            const completedInThisLevel = progress.completedMissions.filter(
                m => level.missions.some(lm => lm.id === m.id)
            ).length;

            if (completedInThisLevel >= level.minToComplete && level.unlocks.length > 0) {
                unlockedLevels.push(...level.unlocks);
            }
        }

        let html = '';

        // Build the Skill Tree HTML
        for (let [levelId, level] of Object.entries(missionTree)) {
            const isUnlocked = unlockedLevels.includes(levelId);
            const completedInLevel = progress.completedMissions.filter(
                m => level.missions.some(lm => lm.id === m.id)
            ).length;
            const levelComplete = completedInLevel >= level.minToComplete;

            html += `<div class="level ${isUnlocked ? '' : 'locked-level'}">`;
            html += `<h2>${level.emoji} ${level.name} ${level.emoji}</h2>`;
            html += `<div class="level-description">${level.description}</div>`;
            html += `<div class="missions-row">`;

            level.missions.forEach((mission, index) => {
                const isCompleted = progress.completedMissions.some(m => m.id === mission.id);
                
                let status = 'locked';
                if (isCompleted) {
                    status = 'completed';
                } else if (isUnlocked) {
                    status = 'available';
                }

                html += `
                    <div class="mission-circle ${status}" data-repo="${mission.repo}">
                        <div class="circle">
                            <span class="circle-number">${mission.number}</span>
                            <span class="circle-points">${mission.points} pts</span>
                        </div>
                        <span class="mission-name">${mission.name}</span>
                        <div class="status-icon">${status === 'completed' ? '✅' : (status === 'available' ? '✨' : '🔒')}</div>
                    </div>
                `;

                if (index < level.missions.length - 1) {
                    html += `<div class="connector">➡️</div>`;
                }
            });

            html += `</div>`; // Close missions-row
            html += `<div class="level-progress">📊 ${completedInLevel}/${level.minToComplete} missions for next level</div>`;
            html += `</div>`; // Close level
            html += `<div class="connector-large">⬇️</div>`;
        }

        document.getElementById('skill-tree').innerHTML = html;

        // Handle Clicks: Only allow clicking on Available or Completed missions
        document.querySelectorAll('.mission-circle.available, .mission-circle.completed').forEach(circle => {
            circle.addEventListener('click', function() {
                const repoName = this.dataset.repo;
                window.open(`https://github.com/codequest-classroom/${repoName}`, '_blank');
            });
        });

    } catch (error) {
        console.error('Error loading progress:', error);
        document.getElementById('skill-tree').innerHTML = `<h2>Complete your first mission to unlock your tree! 🚀</h2>`;
    }
}

// Initial load
loadStudentProgress();

// Refresh every 30 seconds to catch passing grades
setInterval(loadStudentProgress, 30000);
