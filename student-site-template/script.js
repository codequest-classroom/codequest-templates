const username = window.location.hostname.split('.')[0];

// Mission database with level info
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
        pointsPerMission: 5,
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
        pointsPerMission: 8,
        unlocks: []
    }
};

async function loadStudentProgress() {
    try {
        const response = await fetch(
            `https://raw.githubusercontent.com/codequest-classroom/codequest-master/main/students/${username}.json`
        );
        
        if (!response.ok) {
            throw new Error('Student data not found');
        }
        
        const student = await response.json();
        
        let totalXP = student.progress.completedMissions.reduce((sum, m) => sum + m.points, 0);
        
        document.getElementById('student-name').textContent = `${student.student.name}'s Coding Quest 🚀`;
        document.getElementById('xp').textContent = totalXP;
        document.getElementById('badges').textContent = student.progress.badges.length;
        
        let unlockedLevels = ["web-level-1"];
        if (totalXP >= 10) unlockedLevels.push("web-level-2");
        
        let html = '';
        
        // Add floating emojis for fun
        html += `<div class="emoji-cloud">🌟</div>`;
        html += `<div class="emoji-cloud">⭐</div>`;
        html += `<div class="emoji-cloud">🚀</div>`;
        
        // Build each level
        for (let [levelId, level] of Object.entries(missionTree)) {
            const isUnlocked = unlockedLevels.includes(levelId);
            
            const completedInLevel = student.progress.completedMissions.filter(
                m => level.missions.some(lm => lm.id === m.id)
            ).length;
            
            const levelComplete = completedInLevel >= level.minToComplete;
            
            html += `<div class="level">`;
            html += `<h2>${level.emoji} ${level.name} ${level.emoji}</h2>`;
            html += `<div class="level-description">${level.description}</div>`;
            
            // Missions row with circles
            html += `<div class="missions-row">`;
            
            level.missions.forEach((mission, index) => {
                const isCompleted = student.progress.completedMissions.some(m => m.id === mission.id);
                
                let status = 'locked';
                if (isCompleted) {
                    status = 'completed';
                } else if (isUnlocked && !levelComplete) {
                    status = 'available';
                }
                
                html += `<div class="mission-circle ${status}" data-level="${levelId.slice(-1)}" data-repo="${mission.repo}">`;
                html += `<div class="circle">`;
                html += `<span class="circle-number">${mission.number}</span>`;
                html += `<span class="circle-points">${mission.points} pts</span>`;
                html += `</div>`;
                html += `<span class="mission-name">${mission.name}</span>`;
                
                if (status === 'completed') {
                    html += `<div style="font-size: 24px; margin-top: 5px;">✅</div>`;
                } else if (status === 'available') {
                    html += `<div style="font-size: 24px; margin-top: 5px;">✨</div>`;
                } else {
                    html += `<div style="font-size: 24px; margin-top: 5px;">🔒</div>`;
                }
                
                html += `</div>`;
                
                // Add connector arrow between missions (except last)
                if (index < level.missions.length - 1) {
                    html += `<div class="connector">➡️</div>`;
                }
            });
            
            html += `</div>`; // Close missions-row
            
            // Progress indicator
            html += `<div class="level-progress">📊 ${completedInLevel}/${level.minToComplete} missions done`;
            if (levelComplete) {
                html += ` ✅ Level Complete!`;
            }
            html += `</div>`;
            
            // Show what this level unlocks
            if (levelComplete && level.unlocks.length > 0) {
                html += `<div class="unlock-message">🎉 NEW PATH UNLOCKED! 🎉</div>`;
            }
            
            html += `</div>`; // Close level
            
            // Add big arrow between levels
            html += `<div class="connector" style="font-size: 50px;">⬇️</div>`;
        }
        
        document.getElementById('skill-tree').innerHTML = html;
        
        // Add click handlers to available mission circles
        document.querySelectorAll('.mission-circle.available').forEach(circle => {
            circle.addEventListener('click', function() {
                const repoName = this.dataset.repo;
                window.open(`https://github.com/codequest-classroom/${repoName}`, '_blank');
            });
        });
        
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('skill-tree').innerHTML = `
            <div style="text-align: center; padding: 50px; background: rgba(255,255,255,0.2); border-radius: 50px;">
                <h2>🌟 Welcome to your Coding Quest! 🌟</h2>
                <p style="font-size: 24px; margin: 20px;">Complete your first mission to see your skill tree!</p>
                <div style="font-size: 60px;">🚀✨⭐</div>
            </div>
        `;
    }
}

loadStudentProgress();
setInterval(loadStudentProgress, 30000);
