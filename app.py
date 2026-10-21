import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Google Floats Game", page_icon="☁️", layout="wide")

st.markdown("""
    <style>
        .block-container { padding-top: 0.5rem; padding-bottom: 0.5rem; max-width: 1200px; }
        iframe { display: block; margin: 0 auto; border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.25); }
    </style>
""", unsafe_allow_html=True)

st.title("☁️ Trò Chơi Đám Mây Bay ☁️")
st.caption("🥶 trò chơi siêu cấp bá khí - Đã tăng âm lượng toàn bộ âm thanh 🔊 🥶")

game_html = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
<style>
    * {
        box-sizing: border-box;
        -webkit-touch-callout: none;
        -webkit-user-select: none;
        user-select: none;
        touch-action: manipulation;
    }
    body, html { 
        margin: 0; 
        padding: 0; 
        width: 100%; 
        height: 100%; 
        overflow: hidden; 
        background-color: #0284c7; 
        display: flex; 
        justify-content: center; 
        align-items: center; 
        font-family: system-ui, -apple-system, sans-serif;
        outline: none;
    }
    #gameContainer { 
        position: relative; 
        width: 100%; 
        max-width: 960px; 
        height: 100vh; 
        max-height: 540px; 
        overflow: hidden; 
        border-radius: 16px; 
        box-shadow: 0 12px 32px rgba(0, 0, 0, 0.4);
    }
    @media (max-width: 768px) {
        #gameContainer {
            max-width: 100%;
            height: 80vh;
            max-height: 600px;
            border-radius: 12px;
        }
    }
    canvas { 
        width: 100%; 
        height: 100%; 
        display: block; 
        outline: none;
    }
</style>
</head>
<body id="gameBody" tabindex="0">
    <div id="gameContainer">
        <canvas id="gameCanvas" tabindex="1"></canvas>
    </div>

<script>
const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');
const container = document.getElementById('gameContainer');

window.focus();
canvas.focus();

let GAME_WIDTH = 800;
let GAME_HEIGHT = 450;

function resizeCanvas() {
    GAME_WIDTH = container.clientWidth;
    GAME_HEIGHT = container.clientHeight;
    canvas.width = GAME_WIDTH;
    canvas.height = GAME_HEIGHT;
}
resizeCanvas();
window.addEventListener('resize', resizeCanvas);

let cloud = { x: 80, y: 180, width: 55, height: 40, gravity: 0.32, lift: -6.5, velocity: 0, rotation: 0 };
let obstacles = [];
let windParticles = [];
let stars = [];
let frameCount = 0;
let nextObstacleFrame = 60;
let score = 0;
let highScore = localStorage.getItem('google_floats_highscore') || 0;
let gameOver = false;
let gameStarted = false;
let isMuted = false;

let baseSpeed = 4.0;
let obstacleSpeed = 4.0;

let lastFrameTime = performance.now();
let fps = 60;

// ĐO CPS (Clicks Per Second)
let clickTimestamps = [];
let currentCPS = 0;

let shakeTime = 0;
let droppedUmbrella = { x: 0, y: 0, vx: 0, vy: 0, rot: 0 };

let bgCloudX = 0;
let bgHillNearX = 0;

for (let i = 0; i < 45; i++) {
    stars.push({
        x: Math.random() * 960,
        y: Math.random() * 260,
        size: Math.random() * 2 + 1,
        speed: Math.random() * 0.4 + 0.1,
        alpha: Math.random()
    });
}

// --- HỆ THỐNG ÂM THANH (TĂNG ÂM LƯỢNG) ---
let audioCtx = null;
let bgmTimer = null;
let bgmStep = 0;

const chillChords = [
    [220.00, 277.18, 329.63, 415.30],
    [185.00, 220.00, 277.18, 329.63],
    [246.94, 293.66, 369.99, 440.00],
    [164.81, 246.94, 311.13, 392.00]
];

function initAudio() {
    try {
        if (!audioCtx) {
            const AudioContextClass = window.AudioContext || window.webkitAudioContext;
            if (AudioContextClass) audioCtx = new AudioContextClass();
        }
        if (audioCtx && audioCtx.state === 'suspended') {
            audioCtx.resume();
        }
    } catch (e) {
        console.warn("AudioContext init error:", e);
    }
}

function startBGM() {
    if (bgmTimer || isMuted) return;
    bgmStep = 0;
    
    bgmTimer = setInterval(() => {
        if (!gameStarted || gameOver || isMuted || !audioCtx || audioCtx.state !== 'running') return;
        
        try {
            let chordIndex = Math.floor(bgmStep / 4) % chillChords.length;
            let chord = chillChords[chordIndex];
            let noteFreq = chord[bgmStep % 4];

            let osc = audioCtx.createOscillator();
            let gain = audioCtx.createGain();
            osc.type = 'sine';
            osc.frequency.setValueAtTime(noteFreq, audioCtx.currentTime);

            // Tăng âm lượng BGM lên 0.06
            gain.gain.setValueAtTime(0.001, audioCtx.currentTime);
            gain.gain.linearRampToValueAtTime(0.06, audioCtx.currentTime + 0.1);
            gain.gain.exponentialRampToValueAtTime(0.0001, audioCtx.currentTime + 0.8);

            osc.connect(gain);
            gain.connect(audioCtx.destination);

            osc.start();
            osc.stop(audioCtx.currentTime + 0.85);

            bgmStep++;
        } catch (e) {}
    }, 450);
}

function stopBGM() {
    if (bgmTimer) {
        clearInterval(bgmTimer);
        bgmTimer = null;
    }
}

function playJumpSound() {
    if (!audioCtx || isMuted || audioCtx.state !== 'running') return;
    try {
        let osc = audioCtx.createOscillator();
        let gain = audioCtx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(260, audioCtx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(520, audioCtx.currentTime + 0.12);
        
        // Tăng âm lượng tiếng nhảy lên 0.22
        gain.gain.setValueAtTime(0.22, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.12);
        
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start();
        osc.stop(audioCtx.currentTime + 0.12);
    } catch (e) {}
}

function playScoreSound() {
    if (!audioCtx || isMuted || audioCtx.state !== 'running') return;
    try {
        let notes = [523.25, 659.25, 783.99];
        notes.forEach((freq, idx) => {
            let osc = audioCtx.createOscillator();
            let gain = audioCtx.createGain();
            osc.type = 'sine';
            osc.frequency.setValueAtTime(freq, audioCtx.currentTime + idx * 0.05);
            
            // Tăng âm lượng tiếng ghi điểm lên 0.15
            gain.gain.setValueAtTime(0.15, audioCtx.currentTime + idx * 0.05);
            gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + idx * 0.05 + 0.3);
            
            osc.connect(gain);
            gain.connect(audioCtx.destination);
            osc.start(audioCtx.currentTime + idx * 0.05);
            osc.stop(audioCtx.currentTime + idx * 0.05 + 0.3);
        });
    } catch (e) {}
}

function playHitSound() {
    if (!audioCtx || isMuted || audioCtx.state !== 'running') return;
    try {
        let osc = audioCtx.createOscillator();
        let gain = audioCtx.createGain();
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(150, audioCtx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(50, audioCtx.currentTime + 0.35);
        
        // Tăng âm lượng tiếng va chạm lên 0.35
        gain.gain.setValueAtTime(0.35, audioCtx.currentTime);
        gain.gain.linearRampToValueAtTime(0.001, audioCtx.currentTime + 0.35);
        
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start();
        osc.stop(audioCtx.currentTime + 0.35);
    } catch (e) {}
}

function triggerGameOver() {
    gameOver = true;
    shakeTime = 10;
    stopBGM();
    playHitSound();

    if (score > highScore) {
        highScore = score;
        localStorage.setItem('google_floats_highscore', highScore);
    }

    droppedUmbrella = {
        x: cloud.x + 28,
        y: cloud.y - 8,
        vx: 2 + Math.random() * 2,
        vy: -4,
        rot: 0
    };
}

function recordClick() {
    let now = performance.now();
    clickTimestamps.push(now);
}

function handleInput(e) {
    window.focus();
    canvas.focus();

    initAudio();

    if (e) {
        if (e.type === 'keydown') {
            if (e.code === 'Space' || e.key === ' ' || e.keyCode === 32) {
                if (e.preventDefault) e.preventDefault();
            } else {
                return;
            }
        }
        
        if (e.type === 'mousedown' || e.type === 'touchstart') {
            let rect = canvas.getBoundingClientRect();
            let clientX = e.clientX || (e.touches && e.touches[0] ? e.touches[0].clientX : 0);
            let clientY = e.clientY || (e.touches && e.touches[0] ? e.touches[0].clientY : 0);
            
            let x = clientX - rect.left;
            let y = clientY - rect.top;

            if (x > GAME_WIDTH - 70 && y < 60) {
                isMuted = !isMuted;
                if (isMuted) stopBGM();
                else if (gameStarted && !gameOver) startBGM();
                if (e.preventDefault) e.preventDefault();
                return;
            }
        }
    }

    recordClick();
    
    if (gameOver) { resetGame(); return; }
    if (!gameStarted) { 
        gameStarted = true; 
        startBGM();
        loop(); 
    }
    
    cloud.velocity = cloud.lift;
    playJumpSound();

    for (let i = 0; i < 3; i++) {
        windParticles.push({
            x: cloud.x + 15 + Math.random() * 30,
            y: cloud.y + 35,
            vx: -1 - Math.random() * 2,
            vy: 2 + Math.random() * 2,
            life: 1.0,
            size: 3 + Math.random() * 3
        });
    }
}

window.addEventListener('keydown', handleInput, true);
document.addEventListener('keydown', handleInput, true);
canvas.addEventListener('touchstart', handleInput, { passive: false });
canvas.addEventListener('mousedown', handleInput);

function drawBackground() {
    if (gameStarted && !gameOver) {
        bgCloudX = (bgCloudX - (0.7 * (obstacleSpeed / 4))) % GAME_WIDTH;
        bgHillNearX = (bgHillNearX - (2.0 * (obstacleSpeed / 4))) % GAME_WIDTH;
    }

    let scoreCycle = score % 600;
    let nightRatio = 0;

    if (scoreCycle >= 200 && scoreCycle <= 300) {
        nightRatio = (scoreCycle - 200) / 100;
    } else if (scoreCycle > 300 && scoreCycle < 500) {
        nightRatio = 1;
    } else if (scoreCycle >= 500 && scoreCycle <= 600) {
        nightRatio = 1 - (scoreCycle - 500) / 100;
    }

    let topR = Math.round(2 * (1 - nightRatio) + 15 * nightRatio);
    let topG = Math.round(132 * (1 - nightRatio) + 23 * nightRatio);
    let topB = Math.round(199 * (1 - nightRatio) + 42 * nightRatio);

    let botR = Math.round(186 * (1 - nightRatio) + 30 * nightRatio);
    let botG = Math.round(230 * (1 - nightRatio) + 41 * nightRatio);
    let botB = Math.round(253 * (1 - nightRatio) + 89 * nightRatio);

    let skyGrad = ctx.createLinearGradient(0, 0, 0, GAME_HEIGHT);
    skyGrad.addColorStop(0, `rgb(${topR}, ${topG}, ${topB})`);
    skyGrad.addColorStop(1, `rgb(${botR}, ${botG}, ${botB})`);
    ctx.fillStyle = skyGrad;
    ctx.fillRect(0, 0, GAME_WIDTH, GAME_HEIGHT);

    if (nightRatio > 0) {
        ctx.save();
        ctx.globalAlpha = nightRatio;
        
        ctx.shadowColor = '#fef08a';
        ctx.shadowBlur = 20;
        ctx.fillStyle = '#fef08a';
        ctx.beginPath();
        ctx.arc(GAME_WIDTH - 120, 80, 26, 0, Math.PI * 2);
        ctx.fill();
        ctx.shadowBlur = 0;

        ctx.fillStyle = `rgb(${topR}, ${topG}, ${topB})`;
        ctx.beginPath();
        ctx.arc(GAME_WIDTH - 110, 72, 22, 0, Math.PI * 2);
        ctx.fill();

        stars.forEach(s => {
            if (gameStarted && !gameOver) {
                s.x -= s.speed * (obstacleSpeed / 4);
                if (s.x < 0) s.x = GAME_WIDTH + Math.random() * 20;
            }

            ctx.fillStyle = `rgba(255, 255, 255, ${s.alpha * nightRatio})`;
            ctx.beginPath();
            ctx.arc(s.x, s.y, s.size, 0, Math.PI * 2);
            ctx.fill();
            s.alpha += (Math.random() - 0.5) * 0.05;
            s.alpha = Math.max(0.2, Math.min(1, s.alpha));
        });
        ctx.restore();
    }

    let cloudAlpha = 0.45 - nightRatio * 0.25;
    ctx.fillStyle = `rgba(255, 255, 255, ${cloudAlpha})`;
    for (let offset of [bgCloudX, bgCloudX + GAME_WIDTH]) {
        ctx.beginPath();
        ctx.arc(offset + 80, 70, 35, 0, Math.PI * 2);
        ctx.arc(offset + 120, 50, 48, 0, Math.PI * 2);
        ctx.arc(offset + 170, 65, 38, 0, Math.PI * 2);
        ctx.arc(offset + 210, 80, 28, 0, Math.PI * 2);
        ctx.fill();

        ctx.beginPath();
        ctx.arc(offset + 350, 110, 22, 0, Math.PI * 2);
        ctx.arc(offset + 380, 95, 30, 0, Math.PI * 2);
        ctx.arc(offset + 415, 110, 24, 0, Math.PI * 2);
        ctx.fill();

        ctx.beginPath();
        ctx.arc(offset + 560, 60, 40, 0, Math.PI * 2);
        ctx.arc(offset + 610, 40, 55, 0, Math.PI * 2);
        ctx.arc(offset + 670, 55, 42, 0, Math.PI * 2);
        ctx.arc(offset + 720, 75, 30, 0, Math.PI * 2);
        ctx.fill();
    }

    let hillR = Math.round(21 * (1 - nightRatio) + 6 * nightRatio);
    let hillG = Math.round(128 * (1 - nightRatio) + 40 * nightRatio);
    let hillB = Math.round(61 * (1 - nightRatio) + 25 * nightRatio);
    ctx.fillStyle = `rgb(${hillR}, ${hillG}, ${hillB})`;

    for (let offset of [bgHillNearX, bgHillNearX + GAME_WIDTH]) {
        ctx.beginPath();
        ctx.arc(offset + GAME_WIDTH * 0.1, GAME_HEIGHT + 240, GAME_WIDTH * 0.35, 0, Math.PI * 2);
        ctx.arc(offset + GAME_WIDTH * 0.5, GAME_HEIGHT + 255, GAME_WIDTH * 0.38, 0, Math.PI * 2);
        ctx.arc(offset + GAME_WIDTH * 0.88, GAME_HEIGHT + 245, GAME_WIDTH * 0.32, 0, Math.PI * 2);
        ctx.fill();
    }
}

function drawPlayer(x, y) {
    ctx.save();
    ctx.translate(x + 28, y + 20);
    ctx.rotate(cloud.rotation);
    ctx.translate(-(x + 28), -(y + 20));

    if (!gameOver) {
        ctx.fillStyle = '#f59e0b';
        ctx.beginPath();
        ctx.arc(x + 28, y - 8, 20, Math.PI, 0);
        ctx.fill();
        ctx.strokeStyle = '#b45309';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(x + 28, y - 8);
        ctx.lineTo(x + 28, y + 10);
        ctx.stroke();
    }

    ctx.fillStyle = 'white';
    ctx.beginPath();
    ctx.arc(x + 15, y + 20, 14, 0, Math.PI * 2);
    ctx.arc(x + 28, y + 12, 18, 0, Math.PI * 2);
    ctx.arc(x + 42, y + 20, 14, 0, Math.PI * 2);
    ctx.fill();

    if (gameOver) {
        ctx.strokeStyle = '#0f172a';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(x + 20, y + 13); ctx.lineTo(x + 26, y + 19);
        ctx.moveTo(x + 26, y + 13); ctx.lineTo(x + 20, y + 19);
        ctx.stroke();

        ctx.beginPath();
        ctx.moveTo(x + 30, y + 13); ctx.lineTo(x + 36, y + 19);
        ctx.moveTo(x + 36, y + 13); ctx.lineTo(x + 30, y + 19);
        ctx.stroke();

        ctx.beginPath();
        ctx.arc(x + 28, y + 24, 4, Math.PI, 0);
        ctx.stroke();
    } else {
        ctx.fillStyle = '#0f172a';
        ctx.beginPath();
        ctx.arc(x + 23, y + 16, 2.5, 0, Math.PI * 2);
        ctx.arc(x + 33, y + 16, 2.5, 0, Math.PI * 2);
        ctx.fill();

        ctx.strokeStyle = '#0f172a';
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.arc(x + 28, y + 20, 4, 0, Math.PI, false);
        ctx.stroke();
    }

    ctx.restore();
}

function drawDroppedUmbrella() {
    if (!gameOver) return;
    ctx.save();
    ctx.translate(droppedUmbrella.x, droppedUmbrella.y);
    ctx.rotate(droppedUmbrella.rot);

    ctx.fillStyle = '#f59e0b';
    ctx.beginPath();
    ctx.arc(0, 0, 20, Math.PI, 0);
    ctx.fill();

    ctx.strokeStyle = '#b45309';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(0, 0);
    ctx.lineTo(0, 18);
    ctx.stroke();
    ctx.restore();

    droppedUmbrella.x += droppedUmbrella.vx;
    droppedUmbrella.y += droppedUmbrella.vy;
    droppedUmbrella.vy += 0.3;
    droppedUmbrella.rot += 0.15;
}

function drawWindParticles() {
    for (let i = windParticles.length - 1; i >= 0; i--) {
        let p = windParticles[i];
        ctx.fillStyle = `rgba(255, 255, 255, ${p.life})`;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fill();

        p.x += p.vx;
        p.y += p.vy;
        p.life -= 0.05;

        if (p.life <= 0) windParticles.splice(i, 1);
    }
}

function drawCrow(x, y, frame) {
    let wingOffset = Math.sin(frame * 0.18) * 10;
    ctx.fillStyle = '#0f172a';
    ctx.beginPath();
    ctx.ellipse(x + 25, y + 20, 18, 12, 0, 0, Math.PI * 2);
    ctx.fill();

    ctx.beginPath();
    ctx.arc(x + 10, y + 15, 10, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = '#f97316';
    ctx.beginPath();
    ctx.moveTo(x + 3, y + 12);
    ctx.lineTo(x - 10, y + 16);
    ctx.lineTo(x + 3, y + 20);
    ctx.closePath();
    ctx.fill();

    ctx.fillStyle = '#ef4444';
    ctx.beginPath();
    ctx.arc(x + 8, y + 13, 3, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = '#1e293b';
    ctx.beginPath();
    ctx.moveTo(x + 20, y + 16);
    ctx.quadraticCurveTo(x + 30, y - 5 + wingOffset, x + 42, y + 5 + wingOffset);
    ctx.quadraticCurveTo(x + 30, y + 20, x + 20, y + 16);
    ctx.fill();
}

function drawThunderCloud(x, y) {
    ctx.save();
    ctx.shadowColor = '#facc15';
    ctx.shadowBlur = 10;

    ctx.fillStyle = '#334155';
    ctx.beginPath();
    ctx.arc(x + 18, y + 22, 16, 0, Math.PI * 2);
    ctx.arc(x + 32, y + 10, 20, 0, Math.PI * 2);
    ctx.arc(x + 48, y + 22, 16, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = '#facc15';
    ctx.beginPath();
    ctx.moveTo(x + 32, y + 28);
    ctx.lineTo(x + 22, y + 42);
    ctx.lineTo(x + 29, y + 42);
    ctx.lineTo(x + 20, y + 58);
    ctx.lineTo(x + 38, y + 38);
    ctx.lineTo(x + 30, y + 38);
    ctx.closePath();
    ctx.fill();
    ctx.restore();
}

function drawShaders() {
    ctx.save();
    
    let vigGrad = ctx.createRadialGradient(
        GAME_WIDTH / 2, GAME_HEIGHT / 2, GAME_WIDTH * 0.35,
        GAME_WIDTH / 2, GAME_HEIGHT / 2, GAME_WIDTH * 0.7
    );
    vigGrad.addColorStop(0, 'rgba(0,0,0,0)');
    vigGrad.addColorStop(1, 'rgba(0,0,0,0.38)');
    ctx.fillStyle = vigGrad;
    ctx.fillRect(0, 0, GAME_WIDTH, GAME_HEIGHT);

    ctx.fillStyle = 'rgba(255, 255, 255, 0.015)';
    for (let y = 0; y < GAME_HEIGHT; y += 4) {
        ctx.fillRect(0, y, GAME_WIDTH, 1.5);
    }

    ctx.restore();
}

function update() {
    if (gameOver || !gameStarted) return;

    obstacleSpeed = baseSpeed + (score / 100) * 0.3;

    cloud.velocity += cloud.gravity;
    cloud.y += cloud.velocity;
    cloud.rotation = Math.min(Math.PI / 6, Math.max(-Math.PI / 6, cloud.velocity * 0.05));

    if (cloud.y + cloud.height > GAME_HEIGHT - 20 || cloud.y < -10) {
        triggerGameOver();
    }

    frameCount++;
    if (frameCount % 10 === 0) score += 1;

    if (frameCount >= nextObstacleFrame) {
        let type = Math.random() > 0.5 ? 'crow' : 'cloud';
        let obsY = Math.floor(Math.random() * (GAME_HEIGHT - 170)) + 30;
        
        obstacles.push({
            x: GAME_WIDTH,
            y: obsY,
            width: 50,
            height: 40,
            type: type
        });

        let minInterval = Math.max(25, 45 - Math.floor(score / 50));
        let maxInterval = Math.max(50, 105 - Math.floor(score / 40));
        let randomInterval = Math.floor(Math.random() * (maxInterval - minInterval)) + minInterval;
        
        nextObstacleFrame = frameCount + randomInterval;
    }

    for (let i = 0; i < obstacles.length; i++) {
        obstacles[i].x -= obstacleSpeed;

        if (cloud.x + 8 < obstacles[i].x + obstacles[i].width &&
            cloud.x + cloud.width - 8 > obstacles[i].x &&
            cloud.y + 5 < obstacles[i].y + obstacles[i].height &&
            cloud.y + cloud.height - 5 > obstacles[i].y) {
            triggerGameOver();
        }
    }

    if (obstacles.length > 0 && obstacles[0].x < -60) {
        obstacles.shift();
        score += 10;
        playScoreSound();
    }
}

function updateCPS() {
    let now = performance.now();
    clickTimestamps = clickTimestamps.filter(t => now - t <= 1000);
    currentCPS = clickTimestamps.length;
}

function drawUI() {
    updateCPS();

    ctx.save();
    ctx.shadowColor = 'rgba(0,0,0,0.5)';
    ctx.shadowBlur = 3;
    ctx.textAlign = 'left';

    ctx.fillStyle = '#00ffcc';
    ctx.font = 'bold 15px monospace';
    ctx.fillText('FPS  : ' + fps, 15, 28);

    ctx.fillStyle = '#fde047';
    ctx.font = 'bold 14px monospace';
    ctx.fillText('SPEED: ' + obstacleSpeed.toFixed(1) + 'x', 15, 48);

    ctx.fillStyle = '#ff77e9';
    ctx.font = 'bold 14px monospace';
    ctx.fillText('CPS  : ' + currentCPS, 15, 68);

    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 24px monospace';
    ctx.textAlign = 'right';
    ctx.fillText(String(score).padStart(6, '0'), GAME_WIDTH - 80, 38);
    ctx.restore();

    ctx.save();
    ctx.shadowColor = 'rgba(0, 0, 0, 0.4)';
    ctx.shadowBlur = 6;
    
    ctx.fillStyle = 'rgba(255, 255, 255, 0.75)';
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(GAME_WIDTH - 35, 30, 22, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();

    ctx.font = '24px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(isMuted ? '🔇' : '🔊', GAME_WIDTH - 35, 38);
    ctx.restore();

    if (!gameStarted) {
        ctx.fillStyle = 'rgba(0,0,0,0.45)';
        ctx.fillRect(0, 0, GAME_WIDTH, GAME_HEIGHT);
        ctx.fillStyle = 'white';
        ctx.font = 'bold 20px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('👉 BẤM SPACE/CLICK ĐỂ BẮT ĐẦU 👈', GAME_WIDTH / 2, GAME_HEIGHT / 2);
    }

    if (gameOver) {
        ctx.fillStyle = 'rgba(15, 23, 42, 0.75)';
        ctx.fillRect(0, 0, GAME_WIDTH, GAME_HEIGHT);

        let cardW = 320;
        let cardH = 220;
        let cardX = (GAME_WIDTH - cardW) / 2;
        let cardY = (GAME_HEIGHT - cardH) / 2;

        ctx.fillStyle = '#ffffff';
        ctx.shadowColor = 'rgba(0,0,0,0.4)';
        ctx.shadowBlur = 15;
        ctx.beginPath();
        ctx.roundRect(cardX, cardY, cardW, cardH, 16);
        ctx.fill();
        ctx.shadowBlur = 0;

        ctx.fillStyle = '#ef4444';
        ctx.font = 'bold 26px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('GAME OVER!', GAME_WIDTH / 2, cardY + 45);

        ctx.fillStyle = '#334155';
        ctx.font = '16px sans-serif';
        ctx.fillText('Điểm số: ' + score, GAME_WIDTH / 2, cardY + 82);

        ctx.fillStyle = '#d97706';
        ctx.font = 'bold 16px sans-serif';
        ctx.fillText('🏆 Kỷ lục: ' + highScore, GAME_WIDTH / 2, cardY + 112);

        let btnW = 200;
        let btnH = 42;
        let btnX = (GAME_WIDTH - btnW) / 2;
        let btnY = cardY + 145;

        ctx.fillStyle = '#0284c7';
        ctx.beginPath();
        ctx.roundRect(btnX, btnY, btnW, btnH, 20);
        ctx.fill();

        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 15px sans-serif';
        ctx.fillText('🎮Chơi Lại🎮', GAME_WIDTH / 2, btnY + 26);
    }
}

function draw() {
    let now = performance.now();
    let delta = (now - lastFrameTime) / 1000;
    if (delta > 0) {
        fps = Math.round(1 / delta);
    }
    lastFrameTime = now;

    ctx.save();
    if (shakeTime > 0) {
        let dx = (Math.random() - 0.5) * 10;
        let dy = (Math.random() - 0.5) * 10;
        ctx.translate(dx, dy);
        shakeTime--;
    }

    ctx.clearRect(-20, -20, GAME_WIDTH + 40, GAME_HEIGHT + 40);

    drawBackground();
    drawWindParticles();
    drawPlayer(cloud.x, cloud.y);
    drawDroppedUmbrella();

    obstacles.forEach(obs => {
        if (obs.type === 'crow') drawCrow(obs.x, obs.y, frameCount);
        else drawThunderCloud(obs.x, obs.y);
    });

    drawShaders();
    drawUI();
    ctx.restore();
}

function resetGame() {
    cloud.y = GAME_HEIGHT / 2 - 20;
    cloud.velocity = 0;
    cloud.rotation = 0;
    obstacles = [];
    windParticles = [];
    clickTimestamps = [];
    score = 0;
    frameCount = 0;
    nextObstacleFrame = 60;
    obstacleSpeed = baseSpeed;
    gameOver = false;
    gameStarted = true;
    shakeTime = 0;
    startBGM();
    loop();
}

function loop() {
    update();
    draw();
    if (!gameOver && gameStarted) requestAnimationFrame(loop);
}

draw();
</script>
</body>
</html>
"""

components.html(game_html, height=580)
