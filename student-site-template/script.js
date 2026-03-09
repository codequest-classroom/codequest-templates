const username = window.location.hostname.split('.')[0];

// Mission database - only up to CSS-2-3 for demo
const missionTree = {
    "web-level-1": {
        name: "HTML Basics",
        description: "Learn the structure of web pages",
        missions: [
            { id: "html-1-1", name: "HTML Structure", repo: `${username}-html-1-1`, points: 5 },
            { id: "html-1-2", name: "Headings & Paragraphs", repo: `${username}-html-1-2`, points: 5 },
            { id: "html-1-3", name: "Links & Images", repo: `${username}-html-1-3`, points: 5 }
        ],
        minToComplete: 2,
        pointsPerMission: 5,
        unlocks: ["web-level-2"]
    },
    "web-level-2": {
        name: "CSS Basics",
        description: "Make your pages beautiful",
        missions: [
            { id: "css-2-1", name: "CSS Selectors", repo: `${username}-css-2-1`, points: 8 },
            { id: "css-2-2", name: "Box Model", repo: `${username}-css-2-2`, points: 8 },
            { id: "css-2-3", name: "Colors & Fonts", repo: `${username}-css-2-3`, points: 8 }
        ],
        minToComplete: 2,
        pointsPerMission: 8,
        unlocks: [] // Stop here for demo
    }
};

async function loadStudentProgress() {
    try {
        // Fetch student data from master repo
        const response = await fetch(
            `https://raw.githubusercontent.com/codequest-classroom/codequest-master/main/students/${username}.json`
        );
        
        if (!response.ok) {
            throw new Error('Student data not found');
        }
        
        const student = await response.json();
        
        // Calculate total XP
        let totalXP = student.progress.completedMissions.reduce((sum, m) => sum + m.points, 0);
        
        // Update header
        document.getElementById('student-name').textContent = `${student.student.name}'s Coding Quest`;
        document.getElementById('xp').textContent = totalXP;
        document.getElementById('badges').textContent = student.progress.badges.length;
        
        // Calculate unlocked levels based on XP
        let unlockedLevels = ["web-level-1"]; // Level 1 always unlocked
        if (totalXP >= 10) unlockedLevels.push("web-level-2");
        
        let html = '';
        
        // Build each level
        for (let [levelId, level] of Object.entries(missionTree)) {
            const isUnlocked = unlockedLevels.includes(levelId);
            
            // Count completed missions in this level
            const completedInLevel = student.progress.completedMissions.filter(
                m => level.missions.some(lm => lm.id === m.id)
            ).length;
            
            const levelComplete = completedInLevel >= level.minToComplete;
            
            // Level container
            html += `<div class="level ${isUnlocked ? 'unlocked' : 'locked'}">`;
            html += `<h2>${level.name}</h2>`;
            html += `<div class="level-description">${level.description}</div>`;
            
            // Progress bar
            const progressPercent = (completedInLevel / level.minToComplete) * 100;
            html += `<div class="progress-bar">`;
            html += `<div class="progress-fill" style="width: ${progressPercent}%"></div>`;
            html += `</div>`;
            html += `<div class="level-progress">${completedInLevel}/${level.minToComplete} missions completed</div>`;
            
            // Show each mission in this level
            level.missions.forEach(mission => {
                const isCompleted = student.progress.completedMissions.some(m => m.id === mission.id);
                
                let status = 'locked';
                let button = '';
                
                if (isCompleted) {
                    status = 'completed';
                } else if (isUnlocked && !levelComplete) {
                    status = 'available';
                    button = `<button class="start-btn" onclick="openMission('${mission.repo}')">START</button>`;
                }
                
                html += `<div class="mission ${status}">`;
                html += `<span class="mission-name">${mission.name}</span>`;
                html += `<span class="mission-points">${mission.points} pts</span>`;
                html += button;
                html += `</div>`;
            });
            
            // Show what this level unlocks
            if (levelComplete && level.unlocks.length > 0) {
                const nextLevelName = missionTree[level.unlocks[0]].name;
                html += `<div class="next-unlock">✅ Level Complete! Unlocked: ${nextLevelName}</div>`;
            }
            
            html += `</div>`; // Close level
            
            // Add connector between levels
            html += `<div class="level-connector"></div>`;
        }
        
        document.getElementById('skill-tree').innerHTML = html;
        
    } catch (error) {
        console.error('Error loading student data:', error);
        document.getElementById('skill-tree').innerHTML = `
            <div style="text-align: center; padding: 40px;">
                <p>🌟 Welcome to your Coding Quest!</p>
                <p>Complete your first mission to see your progress here.</p>
            </div>
        `;
    }
}

// Function to open mission repo
function openMission(repoName) {
    window.open(`https://github.com/codequest-classroom/${repoName}`, '_blank');
}

// Load progress immediately and every 30 seconds
loadStudentProgress();
setInterval(loadStudentProgress, 30000);
