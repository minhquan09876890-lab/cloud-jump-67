import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Google Floats Game", page_icon="☁️", layout="wide")

st.markdown("""
    <style>
        .block-container { padding-top: 0.5rem; padding-bottom: 0.5rem; max-width: 1200px; }
        iframe { display: block; margin: 0 auto; border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.25); }
    </style>
""", unsafe_allow_html=True)

st.title("☁️ Trò Chơi Đám Mây Bay (Google Floats)")
st.caption("💻 **Phím SPACE / Click chuột trên Máy tính** | 📱 **Chạm màn hình trên Điện thoại**")

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
    }
    #gameContainer { 
        position: relative; 
        width: 100%; 
        max-width: 960px; 
        height: 100vh; 
        max-height: 540px; 
        overflow: hidden; 
        border-radius: 16px; 
        box-shadow: 0 12px 32px rgba(2, 132, 199, 0.25);
        background: linear-gradient(to bottom, #0284c7 0%, #38bdf8 65%, #bae6fd 100%);
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
    }
</style>
</head>
<body tabindex="0">
    <div id="gameContainer">
        <canvas id="gameCanvas"></canvas>
    </div>

<script>
const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');
const container = document.getElementById('gameContainer');

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
let frameCount = 0;
let nextObstacleFrame = 60;
let score = 0;
let gameOver = false;
let gameStarted = false;
let isMuted = false;

// Đếm FPS
let lastFrameTime = performance.now();
let fps = 60;

let shakeTime = 0;
let droppedUmbrella = { x: 0, y: 0, vx: 0, vy: 0, rot: 0 };

let bgCloudX = 0;
let bgHillNearX = 0;

// --- ÂM THANH ---
const AudioCtx = window.AudioContext || window.webkitAudioContext;
let audioCtx = null;
let bgmTimer = null;
let bgmNoteIndex = 0;

const bgmMelody = [
    261.63, 329.63, 392.00, 523.25, 392.00, 329.63,
    293.66, 349.23, 440.00, 587.33, 440.00, 349.23,
    329.63, 392.00, 493.88, 659.25, 493.88, 392.00,
    349.23, 440.00, 523.25, 698.46, 523.25, 440.00
];

function initAudio() {
    if (!audioCtx) audioCtx = new AudioCtx();
    if (audioCtx.state === 'suspended') audioCtx.resume();
}

function startBGM() {
    if (bgmTimer || isMuted) return;
    bgmNoteIndex = 0;
    bgmTimer = setInterval(() => {
        if (!gameStarted || gameOver || isMuted || !audioCtx) return;
        let freq = bgmMelody[bgmNoteIndex];
        let osc = audioCtx.createOscillator();
        let gain = audioCtx.createGain();
        osc.type = 'square';
        osc.frequency.setValueAtTime(freq, audioCtx.currentTime);
        gain.gain.setValueAtTime(0.025, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.18);
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start();
        osc.stop(audioCtx.currentTime + 0.18);
        bgmNoteIndex = (bgmNoteIndex + 1) % bgmMelody.length;
    }, 200);
}

function stopBGM() {
    if (bgmTimer) {
        clearInterval(bgmTimer);
        bgmTimer = null;
    }
}

function playJumpSound() {
    if (!audioCtx || isMuted) return;
    let osc = audioCtx.createOscillator();
    let gain = audioCtx.createGain();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(320, audioCtx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(640, audioCtx.currentTime + 0.1);
    gain.gain.setValueAtTime(0.12, audioCtx.currentTime);
    gain.gain.linearRampToValueAtTime(0.01, audioCtx.currentTime + 0.1);
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.start();
    osc.stop(audioCtx.currentTime + 0.1);
}

function playScoreSound() {
    if (!audioCtx || isMuted) return;
    let osc = audioCtx.createOscillator();
    let gain = audioCtx.createGain();
    osc.type = 'triangle';
    osc.frequency.setValueAtTime(523.25, audioCtx.currentTime);
    osc.frequency.setValueAtTime(659.25, audioCtx.currentTime + 0.08);
    gain.gain.setValueAtTime(0.12, audioCtx.currentTime);
    gain.gain.linearRampToValueAtTime(0.01, audioCtx.currentTime + 0.2);
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.start();
    osc.stop(audioCtx.currentTime + 0.2);
}

function playHitSound() {
    if (!audioCtx || isMuted) return;
    let osc = audioCtx.createOscillator();
    let gain = audioCtx.createGain();
    osc.type = 'sawtooth';
    osc.frequency.setValueAtTime(180, audioCtx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(40, audioCtx.currentTime + 0.3);
    gain.gain.setValueAtTime(0.2, audioCtx.currentTime);
    gain.gain.linearRampToValueAtTime(0.01, audioCtx.currentTime + 0.3);
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.start();
    osc.stop(audioCtx.currentTime + 0.3);
}

function triggerGameOver() {
    gameOver = true;
    shakeTime = 12;
    stopBGM();
    playHitSound();

    droppedUmbrella = {
        x: cloud.x + 28,
        y: cloud.y - 8,
        vx: 3 + Math.random() * 2,
        vy: -5,
        rot: 0
    };
}

// XỬ LÝ SỰ KIỆN PHÍM SPACE VÀ THAO TÁC CHẠM
function handleInput(e) {
    if (e) {
        // Kiểm tra phím bấm
        if (e.type === 'keydown') {
            if (e.code === 'Space' || e.key === ' ' || e.keyCode === 32) {
                if (e.preventDefault) e.preventDefault();
            } else {
                return;
            }
        }
        
        // Kiểm tra bấm nút Mute
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

    initAudio();
    
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

// Đăng ký bắt phím Space trên mọi đối tượng trình duyệt
window.addEventListener('keydown', handleInput, true);
document.addEventListener('keydown', handleInput, true);
canvas.addEventListener('touchstart', handleInput, { passive: false });
canvas.addEventListener('mousedown', handleInput);

function drawBackground() {
    if (gameStarted && !gameOver) {
        bgCloudX = (bgCloudX - 0.7) % GAME_WIDTH;
        bgHillNearX = (bgHillNearX - 2.0) % GAME_WIDTH;
    }

    ctx.fillStyle = 'rgba(255, 255, 255, 0.45)';
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

    ctx.fillStyle = '#15803d';
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
}

function update() {
    if (gameOver || !gameStarted) return;

    cloud.velocity += cloud.gravity;
    cloud.y += cloud.velocity;
    cloud.rotation = Math.min(Math.PI / 6, Math.max(-Math.PI / 6, cloud.velocity * 0.05));

    if (cloud.y + cloud.height > GAME_HEIGHT - 20 || cloud.y < -10) {
        triggerGameOver();
    }

    frameCount++;
    if (frameCount % 10 === 0) score += 1;

    // CHƯỚNG NGẠI VẬT XUẤT HIỆN NGẪU NHIÊN (LOẠI, VỊ TRÍ, KHOẢNG CÁCH)
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

        let randomInterval = Math.floor(Math.random() * 60) + 45;
        nextObstacleFrame = frameCount + randomInterval;
    }

    for (let i = 0; i < obstacles.length; i++) {
        obstacles[i].x -= 4.2;

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

function drawUI() {
    // 1. HIỂN THỊ FPS GÓC TRÊN BÊN TRÁI
    ctx.fillStyle = '#00ffcc';
    ctx.font = 'bold 16px monospace';
    ctx.textAlign = 'left';
    ctx.shadowColor = 'rgba(0,0,0,0.5)';
    ctx.shadowBlur = 3;
    ctx.fillText('FPS: ' + fps, 15, 30);

    // 2. Điểm số góc phải
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 24px monospace';
    ctx.textAlign = 'right';
    ctx.fillText(String(score).padStart(6, '0'), GAME_WIDTH - 80, 38);
    ctx.shadowBlur = 0;

    // 3. Nút Âm Thanh
    ctx.fillStyle = 'rgba(255,255,255,0.25)';
    ctx.beginPath();
    ctx.arc(GAME_WIDTH - 35, 30, 22, 0, Math.PI * 2);
    ctx.fill();
    ctx.font = '20px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(isMuted ? '🔇' : '🔊', GAME_WIDTH - 35, 37);

    if (!gameStarted) {
        ctx.fillStyle = 'rgba(0,0,0,0.45)';
        ctx.fillRect(0, 0, GAME_WIDTH, GAME_HEIGHT);
        ctx.fillStyle = 'white';
        ctx.font = 'bold 20px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('👉 BẤM SPACE HOẶC CHẠM ĐỂ BẮT ĐẦU 👈', GAME_WIDTH / 2, GAME_HEIGHT / 2);
    }

    if (gameOver) {
        ctx.fillStyle = 'rgba(225, 29, 72, 0.88)';
        ctx.fillRect(0, 0, GAME_WIDTH, GAME_HEIGHT);
        ctx.fillStyle = 'white';
        ctx.font = 'bold 28px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('GAME OVER!', GAME_WIDTH / 2, GAME_HEIGHT / 2 - 25);
        ctx.font = '18px sans-serif';
        ctx.fillText('Điểm của bạn: ' + score, GAME_WIDTH / 2, GAME_HEIGHT / 2 + 15);
        ctx.fillText('👉 Bấm Space hoặc Chạm để chơi lại', GAME_WIDTH / 2, GAME_HEIGHT / 2 + 55);
    }
}

function draw() {
    // Tính toán FPS thực tế
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

    drawUI();
    ctx.restore();
}

function resetGame() {
    cloud.y = GAME_HEIGHT / 2 - 20;
    cloud.velocity = 0;
    cloud.rotation = 0;
    obstacles = [];
    windParticles = [];
    score = 0;
    frameCount = 0;
    nextObstacleFrame = 60;
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
