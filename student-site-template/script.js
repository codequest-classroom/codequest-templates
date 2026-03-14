async function loadStudentProgress() {
    try {
        // Get username from config.json (set per-student when repo is created)
        const configRes = await fetch('./config.json');
        const config = await configRes.json();
        const username = config.username;

        // Load the mission tree and student progress in parallel
        // Both served from the public portfolio repo — no auth needed, always fresh via API
        const [pathRes, progressRes] = await Promise.all([
            fetch(
                `https://api.github.com/repos/codequest-classroom/${username}/contents/web-dev.json`,
                { headers: { 'Accept': 'application/vnd.github.v3.raw' } }
            ),
            fetch(
                `https://api.github.com/repos/codequest-classroom/${username}/contents/progress.json`,
                { headers: { 'Accept': 'application/vnd.github.v3.raw' } }
            )
        ]);

        if (!progressRes.ok) throw new Error('Student data not found');
        if (!pathRes.ok) throw new Error('Path config not found');

        const pathConfig = await pathRes.json();
        const data = await progressRes.json();
        const student = data.student;
        const progress = data.progress;

        // Update UI Header
        document.getElementById('student-name').textContent = `${student.name}'s Coding Quest 🚀`;
        document.getElementById('xp').textContent = progress.xp || 0;
        document.getElementById('badges').textContent = progress.badges ? progress.badges.length : 0;

        const completedMissions = progress.completedMissions || [];
        const unlockedMissions = progress.unlockedMissions || [];

        let html = '';

        for (const level of pathConfig.levels) {
            const isLevelUnlocked = (progress.xp || 0) >= level.pointsToUnlock;
            html += `<div class="level ${isLevelUnlocked ? '' : 'locked-level'}">`;
            html += `<h2>${level.emoji} ${level.name} ${level.emoji}</h2>`;
            html += `<div class="level-description">${level.description}</div>`;
            html += `<div class="missions-row">`;

            level.missions.forEach((mission, index) => {
                const missionId = typeof mission === 'string' ? mission : mission.id;
                const missionName = typeof mission === 'string' ? mission : mission.name;
                const missionPoints = typeof mission === 'object' ? mission.points : level.pointsPerMission;
                const missionNumber = typeof mission === 'object' ? mission.number : index + 1;
                const repoName = `${username}-${missionId}`;

                const isCompleted = completedMissions.some(m => m.id === missionId);
                let status = 'locked';
                if (isCompleted) {
                    status = 'completed';
                } else if (unlockedMissions.includes(missionId)) {
                    status = 'available';
                }

                html += `
                    <div class="mission-circle ${status}" data-repo="${repoName}">
                        <div class="circle">
                            <span class="circle-number">${missionNumber}</span>
                            <span class="circle-points">${missionPoints} pts</span>
                        </div>
                        <span class="mission-name">${missionName}</span>
                        <div class="status-icon">${status === 'completed' ? '✅' : (status === 'available' ? '✨' : '🔒')}</div>
                    </div>
                `;

                if (index < level.missions.length - 1) {
                    html += `<div class="connector">➡️</div>`;
                }
            });

            html += `</div>`; // Close missions-row
            html += `<div class="level-progress">🔓 Requires ${level.pointsToUnlock} XP to unlock</div>`;
            html += `</div>`; // Close level
            html += `<div class="connector-large">⬇️</div>`;
        }

        document.getElementById('skill-tree').innerHTML = html;

        // Handle Clicks: only available or completed missions are clickable
        document.querySelectorAll('.mission-circle.available, .mission-circle.completed').forEach(circle => {
            circle.addEventListener('click', function() {
                window.open(`https://github.com/codequest-classroom/${this.dataset.repo}`, '_blank');
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
