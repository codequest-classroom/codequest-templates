const username = window.location.hostname.split('.')[0];

// Mission database
const missionTree = {
    "web-level-1": {
        name: "HTML Basics",
        missions: [
            { id: "html-1-1", name: "HTML Structure", repo: `${username}-html-1-1`, points: 5 },
            { id: "html-1-2", name: "Headings & Paragraphs", repo: `${username}-html-1-2`, points: 5 },
            { id: "html-1-3", name: "Links & Images", repo: `${username}-html-1-3`, points: 5 }
        ],
        minToComplete: 2,
        unlocks: ["web-level-2"]
    },
    "web-level-2": {
        name: "CSS Basics",
        missions: [
            { id: "css-2-1", name: "CSS Selectors", repo: `${username}-css-2-1`, points: 8 },
            { id: "css-2-2", name: "Box Model", repo: `${username}-css-2-2`, points: 8 },
            { id: "css-2-3", name: "Colors & Fonts", repo: `${username}-css-2-3`, points: 8 }
        ],
        minToComplete: 2,
        unlocks: ["web-level-3"]
    },
    "web-level-3": {
        name: "CSS Layout",
        missions: [
            { id: "css-3-1", name: "Flexbox", repo: `${username}-css-3-1`, points: 10 },
            { id: "css-3-2", name: "CSS Grid", repo: `${username}-css-3-2`, points: 10 },
            { id: "css-3-3", name: "Responsive Design", repo: `${username}-css-3-3`, points: 10 }
        ],
        minToComplete: 2,
        unlocks: []
    }
};

async function loadStudentProgress() {
    try {
        const response = await fetch(
            `https://raw.githubusercontent.com/codequest-classroom/codequest-master/main/students/${username}.json`
        );
        const student = await response.json();
        
        let totalXP = student.progress.completedMissions.reduce((sum, m) => sum + m.points, 0);
        
        document.getElementById('student-name').textContent = `${student.student.name}'s Coding Quest`;
        document.getElementById('xp').textContent = totalXP;
        document.getElementById('badges').textContent = student.progress.badges.length;
        
        // Calculate unlocked levels
        let unlockedLevels = ["web-level-1"];
        if (totalXP >= 10) unlockedLevels.push("web-level-2");
        if (totalXP >= 26) unlockedLevels.push("web-level-3");
        
        let html = '';
        
        for (let [levelId, level] of Object.entries(missionTree)) {
            const isUnlocked = unlockedLevels.includes(levelId);
            const completedInLevel = student.progress.completedMissions.filter(
                m => level.missions.some(lm => lm.id === m.id)
            ).length;
            
            const levelComplete = completedInLevel >= level.minToComplete;
            
            html += `<div class="level ${isUnlocked ? 'unlocked' : 'locked'}">`;
            html += `<h2>${level.name}</h2>`;
            html += `<div class="progress">${completedInLevel}/${level.minToComplete} missions completed</div>`;
            
            level.missions.forEach(mission => {
                const isCompleted = student.progress.completedMissions.some(m => m.id === mission.id);
                
                let status = 'locked';
                let icon = '🔒';
                let clickable = false;
                
                if (isCompleted) {
                    status = 'completed';
                    icon = '✅';
                } else if (isUnlocked && !levelComplete) {
                    status = 'available';
                    icon = '🔓';
                    clickable = true;
                }
                
                html += `<div class="mission ${status}">`;
                html += `<span>${icon} ${mission.name}</span>`;
                html += `<span class="points">${mission.points} pts</span>`;
                
                if (clickable) {
                    html += `<button class="start-btn" onclick="openMission('${mission.repo}')">Start Mission</button>`;
                }
                
                html += `</div>`;
            });
            
            if (levelComplete && level.unlocks.length > 0) {
                html += `<div class="unlocks">✅ Unlocks: ${level.unlocks.map(l => missionTree[l].name).join(', ')}</div>`;
            }
            
            html += `</div>`;
            html += `<div class="level-connector"></div>`;
        }
        
        document.getElementById('skill-tree').innerHTML = html;
        
    } catch (error) {
        console.error('Error loading student data:', error);
        document.getElementById('skill-tree').innerHTML = '<p>Error loading progress. Please try again later.</p>';
    }
}

function openMission(repoName) {
    window.open(`https://github.com/codequest-classroom/${repoName}`, '_blank');
}

loadStudentProgress();
setInterval(loadStudentProgress, 30000);
