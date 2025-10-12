from flask import Flask, request, jsonify, session
import random
import time
import threading
import uuid
from collections import defaultdict
import gc
from threading import Lock

app = Flask(__name__)
app.secret_key = 'random_ladder_game_secret_key_2024'

# 각 세션별 게임 상태를 저장하는 딕셔너리
game_sessions = {}
session_lock = Lock()
finish_line = 102
MAX_SESSIONS = 500
SESSION_TIMEOUT = 3600

def get_session_id():
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return session['session_id']

def cleanup_old_sessions():
    current_time = time.time()
    with session_lock:
        expired_sessions = []
        for sid, data in game_sessions.items():
            if current_time - data.get('last_activity', 0) > SESSION_TIMEOUT:
                expired_sessions.append(sid)
        
        for sid in expired_sessions:
            del game_sessions[sid]
        
        if expired_sessions:
            gc.collect()

def init_game_session(session_id):
    with session_lock:
        if len(game_sessions) >= MAX_SESSIONS:
            cleanup_old_sessions()
            if len(game_sessions) >= MAX_SESSIONS:
                oldest_session = min(game_sessions.items(), key=lambda x: x[1].get('last_activity', 0))
                del game_sessions[oldest_session[0]]
        
        if session_id not in game_sessions:
            players = [
                {"name": "플레이어1", "position": 0, "color": "#ff6b6b", "lane": 0, "speed": 1.0},
                {"name": "플레이어2", "position": 0, "color": "#4ecdc4", "lane": 1, "speed": 1.0},
                {"name": "플레이어3", "position": 0, "color": "#45b7d1", "lane": 2, "speed": 1.0},
                {"name": "플레이어4", "position": 0, "color": "#96ceb4", "lane": 3, "speed": 1.0},
                {"name": "플레이어5", "position": 0, "color": "#ffeaa7", "lane": 4, "speed": 1.0}
            ]
            results = ['통과'] * 5
            winner_index = random.randint(0, 4)
            results[winner_index] = '당첨'
            
            game_sessions[session_id] = {
                'players': players,
                'ladder_connections': [],
                'results': results,
                'game_running': False,
                'last_activity': time.time()
            }
        else:
            game_sessions[session_id]['last_activity'] = time.time()
        
        return game_sessions[session_id]

def get_game_session():
    session_id = get_session_id()
    return init_game_session(session_id)

def generate_ladder(game_session):
    game_session['ladder_connections'] = [[] for _ in range(90)]
    
    player_count = len(game_session['players'])
    items_per_lane = max(3, min(5, player_count))
    
    for lane in range(player_count):
        available_positions = list(range(8, 82))
        item_positions = random.sample(available_positions, min(items_per_lane, len(available_positions)))
        
        for pos in item_positions:
            item_type = random.choice(['spinner', 'rocket', 'lightning', 'tornado', 'freeze'])
            game_session['ladder_connections'][pos].append({'type': item_type, 'lane': lane})

@app.route('/')
def index():
    return '''<!DOCTYPE html>
<html>
<head>
    <title>🪜 랜덤 사다리 게임</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: Arial, sans-serif; 
            background: linear-gradient(135deg, #0c0c0c, #1a1a1a, #2d2d30);
            color: #e0e0e0; 
            min-height: 100vh;
            padding: 10px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { text-align: center; margin-bottom: 30px; position: relative; }
        .header h1 { font-size: clamp(2em, 8vw, 3em); margin-bottom: 10px; }
        .sponsor-text {
            background: rgba(255, 107, 107, 0.2);
            border: 2px solid #ff6b6b;
            padding: 8px 12px;
            border-radius: 8px;
            font-size: clamp(10px, 2.5vw, 13px);
            color: #ff6b6b;
            box-shadow: 0 2px 8px rgba(255, 107, 107, 0.3);
            white-space: nowrap;
        }
        .desktop-only {
            position: fixed;
            top: 20px;
            right: 20px;
            min-width: 200px;
            z-index: 999;
        }
        .mobile-only {
            display: none;
            margin: 15px auto 0 auto;
            width: fit-content;
        }
        @media (max-width: 768px) {
            .header { margin-bottom: 20px; }
            .desktop-only { display: none; }
            .mobile-only { display: block; }
            .input-group { gap: 8px; max-width: 100%; margin: 0 0 20px 0; }
            .input-group input { font-size: 14px; padding: 10px; }
            .btn { padding: 10px 15px; font-size: 14px; white-space: nowrap; }
            .players-grid { grid-template-columns: 1fr; gap: 0px; }
            .player-card { padding: 8px; gap: 6px; }
            .preview-ladder { height: 150px; }
            .preview-player { width: 25px; height: 25px; font-size: 10px; }
            .preview-result { font-size: 8px; padding: 2px 4px; }
            .result-area { 
                padding: 8px 0; 
                gap: 0; 
                flex-wrap: nowrap;
                justify-content: space-evenly;
                align-items: center;
                width: 100%;
            }
            .result-box { 
                font-size: 8px; 
                padding: 4px 2px; 
                min-width: 0;
                width: calc(100% / var(--total-players));
                max-width: calc(100% / var(--total-players));
                display: flex; 
                align-items: center; 
                justify-content: center;
                word-break: keep-all;
                overflow: hidden;
                text-align: center;
                flex-shrink: 1;
                flex-grow: 0;
            }
            .container { padding: 8px; }
            .setup-panel { padding: 12px; }
            .game-area { padding: 8px; min-height: 90vh; max-width: 100%; }
            .ladder-container { height: 50vh; margin: 8px 0; }
            .header h1 { font-size: 2em; }
            .progress-bar { margin: 8px 0; }
            .controls { gap: 8px; flex-wrap: wrap; }
            .player-marker { width: 25px; height: 25px; font-size: 12px; }
            .player-name-tag { font-size: 7px; top: -18px; }
            .obstacle { width: 20px; height: 20px; font-size: 12px; }
        }
        @media (min-width: 1200px) {
            .game-area { max-width: 98vw; }
            .ladder-container { height: 75vh; }
        }
        @media (max-width: 480px) {
            .input-group { gap: 5px; }
            .input-group input { font-size: 13px; padding: 8px; }
            .btn { padding: 8px 12px; font-size: 13px; }
            .preview-ladder { height: 120px; }
            .preview-player { width: 20px; height: 20px; font-size: 8px; }
            .result-area { padding: 4px 0; gap: 0; }
            .result-box { font-size: 6px; padding: 2px 1px; min-width: 0; width: calc(100% / var(--total-players)); line-height: 1.2; flex-shrink: 1; }
            .ladder-container { height: 45vh; }
            .game-area { padding: 5px; }
            .header h1 { font-size: 1.6em; }
            .player-marker { width: 20px; height: 20px; font-size: 10px; }
            .obstacle { width: 18px; height: 18px; font-size: 10px; }
            .setup-panel { padding: 8px; }
        }
        .setup-panel {
            background: rgba(0,0,0,0.4);
            padding: 30px;
            border-radius: 20px;
            margin-bottom: 30px;
        }
        .input-group {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            max-width: 500px;
            margin: 0 auto 20px auto;
            flex-wrap: nowrap;
        }
        .input-group input {
            flex: 1;
            padding: 12px;
            border: 2px solid #4ecdc4;
            border-radius: 10px;
            background: rgba(30,30,30,0.9);
            font-size: 16px;
            color: #e0e0e0;
            min-width: 0;
        }
        .btn {
            padding: 12px 25px;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .btn-primary { background: #4ecdc4; color: #1a1a2e; }
        .btn-success { background: #2ecc71; color: #1a1a2e; }
        .btn-danger { background: #e74c3c; color: white; }
        .players-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 15px;
            margin: 20px auto;
            max-width: 900px;
        }
        .player-card {
            background: rgba(0,0,0,0.3);
            padding: 15px;
            border-radius: 15px;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .player-color {
            width: 35px;
            height: 35px;
            border-radius: 50%;
            border: 3px solid rgba(255,255,255,0.9);
            flex-shrink: 0;
        }
        .player-card input {
            flex: 1;
            background: rgba(20,20,20,0.8);
            border: 1px solid rgba(255,255,255,0.3);
            border-radius: 8px;
            padding: 8px;
            color: #e0e0e0;
            font-size: 14px;
        }
        .remove-btn {
            width: 32px;
            height: 32px;
            border: 1px solid #e74c3c;
            border-radius: 50%;
            background: #e74c3c;
            color: white;
            font-size: 16px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .preview-area {
            margin: 30px 0;
            background: rgba(0,0,0,0.2);
            border-radius: 15px;
            padding: 20px;
        }
        .preview-ladder {
            position: relative;
            height: 200px;
            background: rgba(0,0,0,0.3);
            border-radius: 10px;
            overflow: hidden;
        }
        .preview-lane {
            position: absolute;
            width: 3px;
            height: 100%;
            background: linear-gradient(180deg, #2c3e50, #34495e);
        }
        .preview-player {
            position: absolute;
            width: 32px;
            height: 32px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: bold;
            color: #1a1a2e;
            border: 3px solid rgba(255,255,255,0.9);
            top: 10px;
        }
        .preview-result {
            position: absolute;
            bottom: 10px;
            padding: 4px 6px;
            border-radius: 6px;
            font-size: 10px;
            font-weight: bold;
            transform: translateX(-50%);
            white-space: nowrap;
        }
        .preview-winner { background: #2ecc71; color: #1a1a2e; }
        .preview-pass { background: #95a5a6; color: white; }
        .controls {
            text-align: center;
            margin: 20px auto 0 auto;
            display: flex;
            gap: 15px;
            justify-content: center;
            flex-wrap: wrap;
        }
        .game-area {
            background: rgba(0,0,0,0.5);
            border-radius: 20px;
            padding: 20px;
            min-height: 85vh;
            display: none;
            max-width: 95vw;
            margin: 0 auto;
            width: 100%;
        }
        .ladder-container {
            position: relative;
            width: 100%;
            height: 70vh;
            background: rgba(0,0,0,0.3);
            border-radius: 15px;
            overflow: hidden;
            margin: 20px 0;
        }
        .lane {
            position: absolute;
            width: 4px;
            height: 100%;
            background: linear-gradient(180deg, #2c3e50, #34495e);
        }
        .obstacle {
            position: absolute;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
            border: 2px solid rgba(255,255,255,0.8);
            z-index: 50;
        }
        .obstacle-spinner { background: linear-gradient(45deg, #ff6b35, #f7931e); }
        .obstacle-rocket { background: linear-gradient(45deg, #dc143c, #b22222); }
        .obstacle-lightning { background: linear-gradient(45deg, #ffff00, #ffd700); }
        .obstacle-tornado { background: linear-gradient(45deg, #708090, #696969); }
        .obstacle-freeze { background: linear-gradient(45deg, #00bfff, #1e90ff); }
        .player-marker {
            position: absolute;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
            font-weight: bold;
            color: #1a1a2e;
            border: 2px solid rgba(255,255,255,0.9);
            transition: all 0.3s ease;
            z-index: 100;
        }
        .effect-spinner {
            animation: spin 1s linear infinite;
            border-color: #f39c12 !important;
            box-shadow: 0 0 15px rgba(243, 156, 18, 0.6) !important;
        }
        .effect-rocket {
            transform: scale(1.2) !important;
            border-color: #e74c3c !important;
            box-shadow: 0 0 15px rgba(231, 76, 60, 0.6) !important;
        }
        .effect-lightning {
            border-color: #f1c40f !important;
            box-shadow: 0 0 15px rgba(241, 196, 15, 0.8) !important;
            animation: pulse 0.5s ease-in-out infinite alternate;
        }
        .effect-tornado {
            animation: wobble 0.8s ease-in-out infinite;
            border-color: #95a5a6 !important;
            box-shadow: 0 0 15px rgba(149, 165, 166, 0.6) !important;
        }
        .effect-freeze {
            transform: scale(0.9) !important;
            border-color: #3498db !important;
            box-shadow: 0 0 15px rgba(52, 152, 219, 0.6) !important;
            animation: freeze 2s ease-in-out infinite;
        }
        @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
        @keyframes pulse {
            from { transform: scale(1); }
            to { transform: scale(1.1); }
        }
        @keyframes wobble {
            0%, 100% { transform: rotate(0deg); }
            25% { transform: rotate(-3deg); }
            75% { transform: rotate(3deg); }
        }
        @keyframes freeze {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
        .player-name-tag {
            position: absolute;
            top: -25px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0,0,0,0.9);
            padding: 3px 6px;
            border-radius: 6px;
            font-size: 10px;
            white-space: nowrap;
            color: #e0e0e0;
        }
        .result-area {
            display: flex;
            justify-content: space-evenly;
            align-items: center;
            margin-top: 20px;
            padding: 20px;
            background: rgba(0,0,0,0.3);
            border-radius: 15px;
            flex-wrap: nowrap;
            gap: 0;
            width: 100%;
        }
        .result-box {
            flex: 1;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            font-weight: bold;
            font-size: 14px;
            min-width: 60px;
            flex-shrink: 0;
        }
        .result-winner { background: linear-gradient(135deg, #2ecc71, #27ae60); }
        .result-pass { background: linear-gradient(135deg, #95a5a6, #7f8c8d); }
        .progress-bar {
            width: 100%;
            height: 6px;
            background: rgba(0,0,0,0.4);
            border-radius: 3px;
            margin: 15px 0;
            overflow: hidden;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #4ecdc4, #2ecc71);
            width: 0%;
            transition: width 0.3s ease;
            border-radius: 3px;
        }
        .winner-popup {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.9);
            display: none;
            align-items: center;
            justify-content: center;
            z-index: 1000;
        }
        .winner-content {
            background: linear-gradient(135deg, #2ecc71, #27ae60);
            padding: 50px;
            border-radius: 25px;
            text-align: center;
            color: #1a1a2e;
        }

    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🪜 랜덤 사다리 게임</h1>
            <div class="sponsor-text desktop-only">
                <div style="font-weight: bold; margin-bottom: 8px;">☕ 개발자에게 커피 한잔 후원하기</div>
                <img src="/static/kakaopay.png" alt="카카오페이 QR" style="width: 120px; height: auto; border-radius: 6px;">
            </div>
            <p>플레이어를 설정하고 시작 버튼을 눌러 자동 게임을 즐기세요!</p>
            <div class="sponsor-text mobile-only">
                <div style="font-weight: bold; margin-bottom: 4px;">☕ 개발자에게 커피 한잔 후원하기</div>
                <a href="https://qr.kakaopay.com/FLQYOTPkh5dc02170" target="_blank" style="color: #4ecdc4; text-decoration: none; font-size: 10px; word-break: break-all;">https://qr.kakaopay.com/FLQYOTPkh5dc02170</a>
            </div>
        </div>
        
        <div class="setup-panel" id="setupPanel">
            <div class="input-group">
                <input type="text" id="playerName" placeholder="플레이어 이름 입력" maxlength="15">
                <button class="btn btn-primary" onclick="addPlayer()">추가</button>
            </div>
            
            <div class="players-grid" id="playersGrid"></div>
            
            <div class="preview-area">
                <h3 style="text-align: center; margin-bottom: 20px; color: #4ecdc4;">🪜 사다리 미리보기</h3>
                <div class="preview-ladder" id="previewLadder"></div>
            </div>
            
            <div class="controls">
                <button class="btn btn-success" onclick="startGame()">🚀 시작</button>
                <button class="btn btn-danger" onclick="resetGame()">🔄 리셋</button>
            </div>
        </div>
        
        <div class="game-area" id="gameArea">
            <div class="progress-bar">
                <div class="progress-fill" id="progressFill"></div>
            </div>
            <div class="ladder-container" id="ladderContainer"></div>
            <div class="result-area" id="resultArea"></div>
            <div class="controls">
                <button class="btn btn-primary" onclick="backToSetup()">새 게임</button>
            </div>
        </div>
    </div>
    
    <div class="winner-popup" id="winnerPopup">
        <div class="winner-content">
            <h1 style="font-size: 4em; margin-bottom: 20px;">🎉</h1>
            <h2 id="winnerText" style="margin-bottom: 20px; font-size: 2.5em;"></h2>
            <div id="winnerDetails" style="font-size: 1.5em; margin-bottom: 30px;"></div>
            <div style="display: flex; gap: 15px; justify-content: center;">
                <button class="btn btn-success" onclick="showResult()" style="font-size: 18px; padding: 15px 30px;">결과 보기</button>
                <button class="btn btn-primary" onclick="backToSetup()" style="font-size: 18px; padding: 15px 30px;">새 게임</button>
            </div>
        </div>
    </div>
    


    <script>
        let currentPlayers = [];
        let gameInterval = null;
        let gameProgress = 0;
        
        window.onload = function() {
            loadPlayers();
        };
        
        function loadPlayers() {
            fetch('/api/players')
            .then(response => response.json())
            .then(data => {
                currentPlayers = data;
                displayPlayers();
            })
            .catch(error => {
                console.error('플레이어 로드 실패:', error);
            });
        }
        
        function displayPlayers() {
            const grid = document.getElementById('playersGrid');
            grid.innerHTML = currentPlayers.map((player, index) => 
                `<div class="player-card">
                    <div class="player-color" style="background: ${player.color};"></div>
                    <input type="text" value="${player.name}" onchange="updatePlayerName(${index}, this.value)" placeholder="플레이어 이름">
                    ${currentPlayers.length > 2 ? `<button class="remove-btn" onclick="removePlayer(${index})">×</button>` : ''}
                </div>`
            ).join('');
            updatePreview();
        }
        
        function updatePreview() {
            const preview = document.getElementById('previewLadder');
            if (currentPlayers.length < 2) {
                preview.innerHTML = '<div style="text-align: center; padding: 50px; color: rgba(255,255,255,0.5);">최소 2명의 플레이어가 필요합니다</div>';
                return;
            }
            
            preview.innerHTML = '';
            const containerWidth = preview.offsetWidth;
            const laneSpacing = containerWidth / (currentPlayers.length + 1);
            
            fetch('/api/preview_results')
            .then(response => response.json())
            .then(data => {
                currentPlayers.forEach((player, index) => {
                    const lane = document.createElement('div');
                    lane.className = 'preview-lane';
                    lane.style.left = ((index + 1) * laneSpacing) + 'px';
                    preview.appendChild(lane);
                    
                    const marker = document.createElement('div');
                    marker.className = 'preview-player';
                    marker.style.background = player.color;
                    marker.style.left = ((index + 1) * laneSpacing - 15) + 'px';
                    marker.textContent = player.name.charAt(0);
                    preview.appendChild(marker);
                    
                    const result = document.createElement('div');
                    result.className = `preview-result ${data.results[index] === '당첨' ? 'preview-winner' : 'preview-pass'}`;
                    result.style.left = ((index + 1) * laneSpacing) + 'px';
                    result.textContent = result.className.includes('winner') ? '🎉 당첨' : '통과';
                    preview.appendChild(result);
                });
            })
            .catch(error => {
                console.error('미리보기 결과 로드 실패:', error);
            });
        }
        
        function addPlayer() {
            const input = document.getElementById('playerName');
            const name = input.value.trim();
            
            if (!name) {
                alert('플레이어 이름을 입력하세요!');
                return;
            }
            
            // 모바일에서 5명 제한
            const isMobile = window.innerWidth <= 768;
            if (isMobile && currentPlayers.length >= 5) {
                alert('모바일에서는 최대 5명까지만 추가할 수 있습니다!');
                return;
            }
            
            fetch('/api/add_player', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({name: name})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    input.value = '';
                    loadPlayers();
                } else {
                    alert(data.message);
                }
            });
        }
        
        function updatePlayerName(index, name) {
            if (!name.trim()) return;
            
            fetch('/api/update_player', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({index: index, name: name.trim()})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) loadPlayers();
            });
        }
        
        function removePlayer(index) {
            fetch('/api/remove_player', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({index: index})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) loadPlayers();
            });
        }
        
        function resetGame() {
            fetch('/api/reset', {method: 'POST'})
            .then(() => loadPlayers());
        }
        
        function startGame() {
            if (currentPlayers.length < 2) {
                alert('최소 2명의 플레이어가 필요합니다!');
                return;
            }
            
            fetch('/api/start_game', {method: 'POST'})
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('setupPanel').style.display = 'none';
                    document.getElementById('gameArea').style.display = 'block';
                    setupLadder(data.ladder_connections, data.results);
                    startGameLoop(data.results);
                }
            });
        }
        
        function setupLadder(connections, results) {
            const container = document.getElementById('ladderContainer');
            const resultArea = document.getElementById('resultArea');
            container.innerHTML = '';
            resultArea.innerHTML = '';
            
            const playerCount = currentPlayers.length;
            const containerWidth = container.offsetWidth;
            const laneSpacing = containerWidth / (playerCount + 1);
            
            for (let i = 0; i < playerCount; i++) {
                const lane = document.createElement('div');
                lane.className = 'lane';
                lane.style.left = ((i + 1) * laneSpacing) + 'px';
                container.appendChild(lane);
            }
            
            connections.forEach((levelObstacles, level) => {
                levelObstacles.forEach(obstacle => {
                    const obstacleEl = document.createElement('div');
                    obstacleEl.className = `obstacle obstacle-${obstacle.type}`;
                    const containerHeight = container.offsetHeight;
                    
                    obstacleEl.style.left = ((obstacle.lane + 1) * laneSpacing - 15) + 'px';
                    obstacleEl.style.top = ((level / 90) * (containerHeight - 100) + 50) + 'px';
                    
                    if (obstacle.type === 'spinner') {
                        obstacleEl.textContent = '🌀';
                        obstacleEl.title = '뛱뛱이';
                    } else if (obstacle.type === 'rocket') {
                        obstacleEl.textContent = '🚀';
                        obstacleEl.title = '로켓 부스터';
                    } else if (obstacle.type === 'lightning') {
                        obstacleEl.textContent = '⚡';
                        obstacleEl.title = '번개 스피드';
                    } else if (obstacle.type === 'tornado') {
                        obstacleEl.textContent = '🌪️';
                        obstacleEl.title = '토네이도';
                    } else if (obstacle.type === 'freeze') {
                        obstacleEl.textContent = '❄️';
                        obstacleEl.title = '빙결 트랩';
                    }
                    
                    container.appendChild(obstacleEl);
                });
            });
            
            currentPlayers.forEach((player, index) => {
                const marker = document.createElement('div');
                marker.className = 'player-marker';
                marker.id = `player-${index}`;
                marker.style.background = player.color;
                marker.style.left = ((index + 1) * laneSpacing - 20) + 'px';
                marker.style.top = '10px';
                marker.textContent = player.name.charAt(0);
                
                const nameTag = document.createElement('div');
                nameTag.className = 'player-name-tag';
                nameTag.textContent = player.name;
                nameTag.style.color = player.color;
                marker.appendChild(nameTag);
                
                container.appendChild(marker);
            });
            
            updateResultArea(results);
        }
        
        function updateResultArea(results) {
            const resultArea = document.getElementById('resultArea');
            resultArea.innerHTML = '';
            
            // CSS 변수로 플레이어 수 설정
            document.documentElement.style.setProperty('--total-players', results.length);
            
            const isMobile = window.innerWidth <= 768;
            const isSmallMobile = window.innerWidth <= 480;
            
            results.forEach((result, index) => {
                const resultBox = document.createElement('div');
                resultBox.className = result === '당첨' ? 'result-box result-winner' : 'result-box result-pass';
                
                if (isSmallMobile && results.length > 8) {
                    resultBox.textContent = result === '당첨' ? '🎉' : '✓';
                } else if (isMobile && results.length > 6) {
                    resultBox.textContent = result === '당첨' ? '🎉당' : '통';
                } else if (isMobile && results.length > 4) {
                    resultBox.textContent = result === '당첨' ? '🎉당첨' : '통과';
                } else {
                    resultBox.textContent = result === '당첨' ? '🎉 당첨!' : '통과';
                }
                
                resultArea.appendChild(resultBox);
            });
        }
        
        function startGameLoop(currentResults) {
            gameProgress = 0;
            gameInterval = setInterval(() => {
                fetch('/api/game_status')
                .then(response => response.json())
                .then(data => {
                    if (!data.running) {
                        clearInterval(gameInterval);
                        showWinner(data.winner);
                        return;
                    }
                    
                    if (JSON.stringify(currentResults) !== JSON.stringify(data.results)) {
                        currentResults = data.results;
                        updateResultArea(data.results);
                    }
                    
                    updateGame(data.players);
                    gameProgress = Math.min((data.players[0].position / 100) * 100, 100);
                    document.getElementById('progressFill').style.width = gameProgress + '%';
                });
            }, 200);
        }
        
        function updateGame(players) {
            const container = document.getElementById('ladderContainer');
            const containerWidth = container.offsetWidth;
            const laneSpacing = containerWidth / (players.length + 1);
            
            players.forEach((player, index) => {
                const marker = document.getElementById(`player-${index}`);
                if (marker) {
                    const progress = player.position / 100;
                    const containerHeight = container.offsetHeight;
                    
                    marker.style.left = ((player.lane + 1) * laneSpacing - 20) + 'px';
                    marker.style.top = (10 + progress * (containerHeight - 50)) + 'px';
                    
                    marker.classList.remove('effect-spinner', 'effect-rocket', 'effect-lightning', 'effect-tornado', 'effect-freeze');
                    
                    if (player.spinner_effect > 0) {
                        marker.classList.add('effect-spinner');
                    } else if (player.rocket_effect > 0) {
                        marker.classList.add('effect-rocket');
                    } else if (player.lightning_effect > 0) {
                        marker.classList.add('effect-lightning');
                    } else if (player.tornado_effect > 0) {
                        marker.classList.add('effect-tornado');
                    } else if (player.freeze_effect > 0) {
                        marker.classList.add('effect-freeze');
                    }
                }
            });
        }
        
        let gameEnded = false;
        
        function showWinner(winner) {
            if (!gameEnded) {
                document.getElementById('winnerText').textContent = `${winner.name} 당첨!`;
                document.getElementById('winnerDetails').textContent = '🎉 축하합니다! 🎉';
                document.getElementById('winnerPopup').style.display = 'flex';
                gameEnded = true;
            }
        }
        
        function showResult() {
            document.getElementById('winnerPopup').style.display = 'none';
        }
        
        function backToSetup() {
            document.getElementById('setupPanel').style.display = 'block';
            document.getElementById('gameArea').style.display = 'none';
            document.getElementById('winnerPopup').style.display = 'none';
            gameEnded = false;
            if (gameInterval) {
                clearInterval(gameInterval);
                gameInterval = null;
            }
            fetch('/api/reset', {method: 'POST'})
            .then(() => loadPlayers());
        }
        
        document.getElementById('playerName').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                addPlayer();
            }
        });
        

    </script>
</body>
</html>'''

@app.route('/api/players')
def get_players():
    game_session = get_game_session()
    return jsonify(game_session['players'])

@app.route('/api/add_player', methods=['POST'])
def add_player():
    game_session = get_game_session()
    data = request.get_json()
    name = data.get('name', '').strip()
    
    if not name:
        return jsonify({'success': False, 'message': '이름을 입력하세요!'})
    
    if len(game_session['players']) >= 10:
        return jsonify({'success': False, 'message': '최대 10명까지 가능합니다!'})
    
    colors = ["#ff6b6b", "#4ecdc4", "#45b7d1", "#96ceb4", "#ffeaa7", "#fd79a8", "#fdcb6e", "#6c5ce7", "#a29bfe", "#e17055"]
    
    new_player = {
        "name": name,
        "position": 0,
        "color": colors[len(game_session['players']) % len(colors)],
        "lane": len(game_session['players']),
        "speed": 1.0
    }
    
    game_session['players'].append(new_player)
    
    game_session['results'] = ['통과'] * len(game_session['players'])
    winner_index = random.randint(0, len(game_session['players']) - 1)
    game_session['results'][winner_index] = '당첨'
    
    return jsonify({'success': True})

@app.route('/api/update_player', methods=['POST'])
def update_player():
    game_session = get_game_session()
    data = request.get_json()
    index = data.get('index')
    name = data.get('name', '').strip()
    
    if 0 <= index < len(game_session['players']) and name:
        game_session['players'][index]['name'] = name
        return jsonify({'success': True})
    
    return jsonify({'success': False})

@app.route('/api/remove_player', methods=['POST'])
def remove_player():
    game_session = get_game_session()
    data = request.get_json()
    index = data.get('index')
    
    if len(game_session['players']) <= 2:
        return jsonify({'success': False, 'message': '최소 2명의 플레이어가 필요합니다!'})
    
    if 0 <= index < len(game_session['players']):
        game_session['players'].pop(index)
        for i, player in enumerate(game_session['players']):
            player['lane'] = i
        
        game_session['results'] = ['통과'] * len(game_session['players'])
        winner_index = random.randint(0, len(game_session['players']) - 1)
        game_session['results'][winner_index] = '당첨'
        
        return jsonify({'success': True})
    
    return jsonify({'success': False})

@app.route('/api/reset', methods=['POST'])
def reset_game():
    game_session = get_game_session()
    game_session['game_running'] = False
    
    for i, player in enumerate(game_session['players']):
        player['position'] = 0
        player['lane'] = i
        player['speed'] = 1.0
        for effect in ['spinner_effect', 'rocket_effect', 'lightning_effect', 'tornado_effect', 'freeze_effect', 'spinner_count']:
            if effect in player:
                del player[effect]
    
    game_session['results'] = ['통과'] * len(game_session['players'])
    winner_index = random.randint(0, len(game_session['players']) - 1)
    game_session['results'][winner_index] = '당첨'
    
    return jsonify({'success': True})

@app.route('/api/preview_results')
def preview_results():
    game_session = get_game_session()
    return jsonify({'results': game_session['results']})

@app.route('/api/start_game', methods=['POST'])
def start_game():
    game_session = get_game_session()
    
    if len(game_session['players']) < 2:
        return jsonify({'success': False, 'message': '최소 2명의 플레이어가 필요합니다!'})
    
    game_session['game_running'] = True
    
    for i, player in enumerate(game_session['players']):
        player['position'] = 0
        player['lane'] = i
        player['speed'] = 1.0
        for effect in ['spinner_effect', 'rocket_effect', 'lightning_effect', 'tornado_effect', 'freeze_effect', 'spinner_count']:
            if effect in player:
                del player[effect]
    
    generate_ladder(game_session)
    session_id = get_session_id()
    threading.Thread(target=game_loop, args=(session_id,), daemon=True).start()
    
    return jsonify({'success': True, 'ladder_connections': game_session['ladder_connections'], 'results': game_session['results']})

@app.route('/api/game_status')
def game_status():
    game_session = get_game_session()
    winner = None
    if not game_session['game_running'] and game_session['players']:
        winner_lane = None
        for i, result in enumerate(game_session['results']):
            if result == '당첨':
                winner_lane = i
                break
        
        if winner_lane is not None:
            for player in game_session['players']:
                if player['lane'] == winner_lane and player['position'] >= 102:
                    winner = player
                    break
    
    return jsonify({
        'running': game_session['game_running'],
        'players': game_session['players'],
        'winner': winner,
        'results': game_session['results']
    })

def update_game(session_id):
    if session_id not in game_sessions:
        return
    
    game_session = game_sessions[session_id]
    if not game_session['game_running']:
        return
    
    for player in game_session['players']:
        if 'spinner_effect' in player and player['spinner_effect'] > 0:
            player['spinner_effect'] -= 1
            near_finish_spinner = player['position'] >= (finish_line - 2.5)
            if not near_finish_spinner and player['spinner_count'] > 0 and player['spinner_effect'] % 3 == 0:
                available_lanes = [i for i in range(len(game_session['players'])) if i != player['lane']]
                if available_lanes:
                    new_lane = random.choice(available_lanes)
                    for other_player in game_session['players']:
                        if other_player['lane'] == new_lane:
                            other_player['lane'] = player['lane']
                            break
                    player['lane'] = new_lane
                    player['spinner_count'] -= 1
        
        if 'rocket_effect' in player and player['rocket_effect'] > 0:
            player['rocket_effect'] -= 1
        
        if 'lightning_effect' in player and player['lightning_effect'] > 0:
            player['lightning_effect'] -= 1
        
        if 'tornado_effect' in player and player['tornado_effect'] > 0:
            player['tornado_effect'] -= 1
        
        if 'freeze_effect' in player and player['freeze_effect'] > 0:
            player['freeze_effect'] -= 1
        
        player['speed'] = 1.0
        near_finish = player['position'] >= (finish_line - 2.5)
        
        if not near_finish and random.random() < 0.3:
            available_lanes = [i for i in range(len(game_session['players'])) if i != player['lane']]
            if available_lanes:
                new_lane = random.choice(available_lanes)
                for other_player in game_session['players']:
                    if other_player['lane'] == new_lane:
                        other_player['lane'] = player['lane']
                        break
                player['lane'] = new_lane
        
        player['position'] += 1.1
        
        current_level = int(player['position'])
        if current_level < len(game_session['ladder_connections']):
            obstacles = game_session['ladder_connections'][current_level]
            
            for obstacle in obstacles:
                if player['lane'] == obstacle['lane'] and abs(player['position'] - current_level) < 1:
                    if obstacle['type'] == 'spinner':
                        player['spinner_effect'] = 10
                        player['spinner_count'] = 8
                    elif obstacle['type'] == 'rocket':
                        player['rocket_effect'] = 10
                    elif obstacle['type'] == 'lightning':
                        player['lightning_effect'] = 10
                    elif obstacle['type'] == 'tornado':
                        if not near_finish:
                            lanes = list(range(len(game_session['players'])))
                            random.shuffle(lanes)
                            for i, p in enumerate(game_session['players']):
                                p['lane'] = lanes[i]
                        player['tornado_effect'] = 10
                    elif obstacle['type'] == 'freeze':
                        player['freeze_effect'] = 10
    
    winner_lane = -1
    for i, result in enumerate(game_session['results']):
        if result == '당첨':
            winner_lane = i
            break
    
    if winner_lane >= 0:
        for player in game_session['players']:
            if player['lane'] == winner_lane and player['position'] >= 102:
                game_session['game_running'] = False
                return

def game_loop(session_id):
    update_interval = 0.15
    while session_id in game_sessions and game_sessions[session_id]['game_running']:
        try:
            update_game(session_id)
            if session_id not in game_sessions or not game_sessions[session_id]['game_running']:
                break
            time.sleep(update_interval)
        except Exception:
            if session_id in game_sessions:
                game_sessions[session_id]['game_running'] = False
            break

def background_cleanup():
    while True:
        time.sleep(300)
        cleanup_old_sessions()

if __name__ == '__main__':
    cleanup_thread = threading.Thread(target=background_cleanup, daemon=True)
    cleanup_thread.start()
    
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port, threaded=True)