from flask import Flask, request, jsonify, session
import random
import time
import threading
import uuid
from collections import defaultdict
import gc
from threading import Lock

app = Flask(__name__)
app.secret_key = 'random_games_secret_key_2024'

# 각 세션별 게임 상태를 저장하는 딕셔너리
game_sessions = {}
session_lock = Lock()
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

def init_game_session(session_id, game_type):
    with session_lock:
        if len(game_sessions) >= MAX_SESSIONS:
            cleanup_old_sessions()
            if len(game_sessions) >= MAX_SESSIONS:
                oldest_session = min(game_sessions.items(), key=lambda x: x[1].get('last_activity', 0))
                del game_sessions[oldest_session[0]]
        
        if session_id not in game_sessions:
            if game_type == 'dice':
                players = [
                    {"name": "플레이어1", "color": "#ff6b6b", "dice1": 0, "dice2": 0, "total": 0},
                    {"name": "플레이어2", "color": "#4ecdc4", "dice1": 0, "dice2": 0, "total": 0}
                ]
                game_sessions[session_id] = {
                    'game_type': 'dice',
                    'players': players,
                    'game_running': False,
                    'current_player': 0,
                    'dice_rolling': False,
                    'game_finished': False,
                    'winner': None,
                    'round_number': 1,
                    'tie_breaker_players': [],
                    'is_tie_breaker': False,
                    'last_activity': time.time()
                }
            else:  # roulette
                players = [
                    {"name": "플레이어1", "color": "#ff6b6b"},
                    {"name": "플레이어2", "color": "#4ecdc4"}
                ]
                game_sessions[session_id] = {
                    'game_type': 'roulette',
                    'players': players,
                    'game_running': False,
                    'roulette_spinning': False,
                    'game_finished': False,
                    'winner': None,
                    'winner_index': -1,
                    'spin_angle': 0,
                    'last_activity': time.time()
                }
        else:
            game_sessions[session_id]['last_activity'] = time.time()
        
        return game_sessions[session_id]

def get_game_session(game_type='dice'):
    session_id = get_session_id()
    return init_game_session(session_id, game_type)

@app.route('/')
def index():
    return '''<!DOCTYPE html>
<html>
<head>
    <title>🎮 랜덤 게임 선택</title>
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
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container { max-width: 800px; margin: 0 auto; text-align: center; }
        .header { margin-bottom: 50px; }
        .header h1 { font-size: clamp(2.5em, 10vw, 4em); margin-bottom: 20px; }
        .game-selection {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
            margin: 40px 0;
        }
        .game-card {
            background: rgba(0,0,0,0.4);
            padding: 40px 30px;
            border-radius: 25px;
            cursor: pointer;
            transition: all 0.3s ease;
            border: 3px solid transparent;
        }
        .game-card:hover {
            transform: translateY(-10px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.5);
        }
        .dice-card {
            border-color: #4ecdc4;
            background: linear-gradient(135deg, rgba(78, 205, 196, 0.1), rgba(0,0,0,0.4));
        }
        .dice-card:hover {
            border-color: #4ecdc4;
            box-shadow: 0 20px 40px rgba(78, 205, 196, 0.3);
        }
        .roulette-card {
            border-color: #ff6b6b;
            background: linear-gradient(135deg, rgba(255, 107, 107, 0.1), rgba(0,0,0,0.4));
        }
        .roulette-card:hover {
            border-color: #ff6b6b;
            box-shadow: 0 20px 40px rgba(255, 107, 107, 0.3);
        }
        .game-icon {
            font-size: 4em;
            margin-bottom: 20px;
        }
        .game-title {
            font-size: 1.8em;
            font-weight: bold;
            margin-bottom: 15px;
        }
        .game-description {
            font-size: 1.1em;
            opacity: 0.8;
            line-height: 1.5;
        }
        @media (max-width: 768px) {
            .game-selection { grid-template-columns: 1fr; gap: 20px; }
            .game-card { padding: 30px 20px; }
            .game-icon { font-size: 3em; }
            .game-title { font-size: 1.5em; }
            .game-description { font-size: 1em; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎮 랜덤 게임</h1>
            <p>원하는 게임을 선택하세요!</p>
        </div>
        
        <div class="game-selection">
            <div class="game-card dice-card" onclick="selectGame('dice')">
                <div class="game-icon">🎲</div>
                <div class="game-title">랜덤 주사위 게임</div>
                <div class="game-description">
                    주사위 2개를 굴려서<br>
                    가장 낮은 합계가 나온<br>
                    플레이어가 승리!
                </div>
            </div>
            
            <div class="game-card roulette-card" onclick="selectGame('roulette')">
                <div class="game-icon">🎡</div>
                <div class="game-title">랜덤 룰렛 게임</div>
                <div class="game-description">
                    3D 룰렛을 돌려서<br>
                    룰렛이 가리키는<br>
                    플레이어가 승리!
                </div>
            </div>
        </div>
    </div>

    <script>
        function selectGame(gameType) {
            if (gameType === 'dice') {
                window.location.href = '/dice';
            } else if (gameType === 'roulette') {
                window.location.href = '/roulette';
            }
        }
    </script>
</body>
</html>'''

@app.route('/dice')
def dice_game():
    return '''<!DOCTYPE html>
<html>
<head>
    <title>🎲 랜덤 주사위 게임</title>
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
        .back-btn {
            position: absolute;
            left: 0;
            top: 0;
            background: #4ecdc4;
            color: #1a1a2e;
            padding: 10px 20px;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            font-weight: bold;
        }
        @media (max-width: 768px) {
            .header { margin-bottom: 20px; }
            .input-group { gap: 8px; max-width: 100%; margin: 0 0 20px 0; }
            .input-group input { font-size: 14px; padding: 10px; }
            .btn { padding: 10px 15px; font-size: 14px; white-space: nowrap; }
            .players-grid { grid-template-columns: 1fr; gap: 10px; }
            .player-card { padding: 8px; gap: 6px; }
            .dice-area { padding: 20px 10px; }
            .dice-container { gap: 15px; }
            .dice { width: 60px; height: 60px; font-size: 24px; }
            .container { padding: 8px; }
            .setup-panel { padding: 12px; }
            .game-area { padding: 8px; min-height: 90vh; max-width: 100%; }
            .header h1 { font-size: 2em; }
        }
        @media (max-width: 480px) {
            .input-group { gap: 5px; }
            .input-group input { font-size: 13px; padding: 8px; }
            .btn { padding: 8px 12px; font-size: 13px; }
            .dice { width: 50px; height: 50px; font-size: 20px; }
            .game-area { padding: 5px; }
            .header h1 { font-size: 1.6em; }
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
        .dice-area {
            background: rgba(0,0,0,0.3);
            border-radius: 15px;
            padding: 30px;
            margin: 20px 0;
            text-align: center;
        }
        .current-player {
            font-size: 1.5em;
            margin-bottom: 20px;
            color: #4ecdc4;
        }
        .dice-container {
            display: flex;
            justify-content: center;
            gap: 30px;
            margin: 30px 0;
        }
        .dice {
            width: 80px;
            height: 80px;
            background: white;
            border-radius: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 36px;
            font-weight: bold;
            color: #333;
            border: 3px solid #ddd;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
            transition: all 0.3s ease;
        }
        .dice.rolling {
            animation: roll 0.5s ease-in-out infinite;
            background: linear-gradient(45deg, #ff6b6b, #4ecdc4);
            color: white;
        }
        @keyframes roll {
            0%, 100% { transform: rotate(0deg) scale(1); }
            25% { transform: rotate(90deg) scale(1.1); }
            50% { transform: rotate(180deg) scale(1); }
            75% { transform: rotate(270deg) scale(1.1); }
        }
        .dice-total {
            font-size: 2em;
            margin: 20px 0;
            color: #2ecc71;
            font-weight: bold;
        }
        .players-results {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .player-result {
            background: rgba(0,0,0,0.3);
            padding: 20px;
            border-radius: 15px;
            text-align: center;
            border: 2px solid transparent;
        }
        .player-result.current {
            border-color: #4ecdc4;
            box-shadow: 0 0 15px rgba(78, 205, 196, 0.3);
        }
        .player-result.winner {
            border-color: #2ecc71;
            background: rgba(46, 204, 113, 0.2);
            box-shadow: 0 0 15px rgba(46, 204, 113, 0.5);
        }
        .player-name {
            font-size: 1.2em;
            margin-bottom: 10px;
            font-weight: bold;
        }
        .player-dice {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin: 10px 0;
        }
        .small-dice {
            width: 30px;
            height: 30px;
            background: white;
            border-radius: 5px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
            font-weight: bold;
            color: #333;
        }
        .player-total {
            font-size: 1.5em;
            font-weight: bold;
            color: #4ecdc4;
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
            <button class="back-btn" onclick="goHome()">← 홈</button>
            <h1>🎲 랜덤 주사위 게임</h1>
            <p>플레이어를 설정하고 시작 버튼을 눌러 자동 게임을 즐기세요!</p>
        </div>
        
        <div class="setup-panel" id="setupPanel">
            <div class="input-group">
                <input type="text" id="playerName" placeholder="플레이어 이름 입력" maxlength="15">
                <button class="btn btn-primary" onclick="addPlayer()">추가</button>
            </div>
            
            <div class="players-grid" id="playersGrid"></div>
            
            <div class="controls">
                <button class="btn btn-success" onclick="startGame()">🚀 시작</button>
                <button class="btn btn-danger" onclick="resetGame()">🔄 리셋</button>
            </div>
        </div>
        
        <div class="game-area" id="gameArea">
            <div class="dice-area">
                <div class="current-player" id="currentPlayer">플레이어1의 차례</div>
                <div class="dice-container">
                    <div class="dice" id="dice1">?</div>
                    <div class="dice" id="dice2">?</div>
                </div>
                <div class="dice-total" id="diceTotal">합계: 0</div>
            </div>
            
            <div class="players-results" id="playersResults"></div>
            
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
        
        window.onload = function() {
            loadPlayers();
        };
        
        function goHome() {
            window.location.href = '/';
        }
        
        function loadPlayers() {
            fetch('/api/dice/players')
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
        }
        
        function addPlayer() {
            const input = document.getElementById('playerName');
            const name = input.value.trim();
            
            if (!name) {
                alert('플레이어 이름을 입력하세요!');
                return;
            }
            
            if (currentPlayers.length >= 7) {
                alert('최대 7명까지만 추가할 수 있습니다!');
                return;
            }
            
            fetch('/api/dice/add_player', {
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
            
            fetch('/api/dice/update_player', {
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
            fetch('/api/dice/remove_player', {
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
            fetch('/api/dice/reset', {method: 'POST'})
            .then(() => loadPlayers());
        }
        
        function startGame() {
            if (currentPlayers.length < 2) {
                alert('최소 2명의 플레이어가 필요합니다!');
                return;
            }
            
            fetch('/api/dice/start_game', {method: 'POST'})
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('setupPanel').style.display = 'none';
                    document.getElementById('gameArea').style.display = 'block';
                    startGameLoop();
                }
            });
        }
        
        function startGameLoop() {
            gameInterval = setInterval(() => {
                fetch('/api/dice/game_status')
                .then(response => response.json())
                .then(data => {
                    updateGameDisplay(data);
                    
                    if (data.game_finished) {
                        clearInterval(gameInterval);
                        showWinner(data.winner);
                    }
                });
            }, 500);
        }
        
        function updateGameDisplay(data) {
            let currentPlayerText = '';
            if (data.is_tie_breaker) {
                const tiePlayerNames = data.tie_breaker_players.map(i => data.players[i].name).join(', ');
                currentPlayerText = `재경기 ${data.round_number}라운드 - ${tiePlayerNames}`;
                if (data.current_player < data.tie_breaker_players.length) {
                    const currentIdx = data.tie_breaker_players[data.current_player];
                    currentPlayerText += ` (${data.players[currentIdx].name}의 차례)`;
                }
            } else {
                currentPlayerText = `${data.round_number}라운드`;
                if (data.current_player < data.players.length) {
                    currentPlayerText += ` - ${data.players[data.current_player].name}의 차례`;
                }
            }
            document.getElementById('currentPlayer').textContent = currentPlayerText;
            
            const dice1 = document.getElementById('dice1');
            const dice2 = document.getElementById('dice2');
            const diceTotal = document.getElementById('diceTotal');
            
            if (data.dice_rolling) {
                dice1.className = 'dice rolling';
                dice2.className = 'dice rolling';
                dice1.textContent = '?';
                dice2.textContent = '?';
                diceTotal.textContent = '굴리는 중...';
            } else {
                let currentPlayerIdx = -1;
                if (data.is_tie_breaker && data.current_player < data.tie_breaker_players.length) {
                    currentPlayerIdx = data.tie_breaker_players[data.current_player];
                } else if (!data.is_tie_breaker && data.current_player < data.players.length) {
                    currentPlayerIdx = data.current_player;
                }
                
                if (currentPlayerIdx >= 0) {
                    const currentPlayer = data.players[currentPlayerIdx];
                    dice1.className = 'dice';
                    dice2.className = 'dice';
                    dice1.textContent = currentPlayer.dice1 || '?';
                    dice2.textContent = currentPlayer.dice2 || '?';
                    diceTotal.textContent = `합계: ${currentPlayer.total || 0}`;
                }
            }
            
            updatePlayersResults(data.players, data);
        }
        
        function updatePlayersResults(players, data) {
            const resultsContainer = document.getElementById('playersResults');
            resultsContainer.innerHTML = players.map((player, index) => {
                let className = 'player-result';
                
                if (data.is_tie_breaker) {
                    if (data.current_player < data.tie_breaker_players.length && 
                        index === data.tie_breaker_players[data.current_player] && !data.winner) {
                        className += ' current';
                    }
                } else {
                    if (index === data.current_player && !data.winner) {
                        className += ' current';
                    }
                }
                
                if (data.winner && player.name === data.winner.name) {
                    className += ' winner';
                }
                
                let playerNameText = player.name;
                if (data.is_tie_breaker && data.tie_breaker_players.includes(index)) {
                    playerNameText += ' (재경기)';
                }
                
                return `
                    <div class="${className}">
                        <div class="player-name" style="color: ${player.color};">${playerNameText}</div>
                        <div class="player-dice">
                            <div class="small-dice">${player.dice1 || '?'}</div>
                            <div class="small-dice">${player.dice2 || '?'}</div>
                        </div>
                        <div class="player-total">합계: ${player.total || 0}</div>
                    </div>
                `;
            }).join('');
        }
        
        function showWinner(winner) {
            document.getElementById('winnerText').textContent = `${winner.name} 당첨!`;
            document.getElementById('winnerDetails').textContent = 
                `주사위 합계: ${winner.total} (가장 낮은 점수!)`;
            document.getElementById('winnerPopup').style.display = 'flex';
        }
        
        function showResult() {
            document.getElementById('winnerPopup').style.display = 'none';
        }
        
        function backToSetup() {
            document.getElementById('setupPanel').style.display = 'block';
            document.getElementById('gameArea').style.display = 'none';
            document.getElementById('winnerPopup').style.display = 'none';
            if (gameInterval) {
                clearInterval(gameInterval);
                gameInterval = null;
            }
            fetch('/api/dice/reset', {method: 'POST'})
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