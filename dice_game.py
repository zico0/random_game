from flask import Flask, request, jsonify, session
import random
import time
import threading
import uuid
from collections import defaultdict
import gc
from threading import Lock

app = Flask(__name__)
app.secret_key = 'random_dice_game_secret_key_2024'

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

def init_game_session(session_id):
    with session_lock:
        if len(game_sessions) >= MAX_SESSIONS:
            cleanup_old_sessions()
            if len(game_sessions) >= MAX_SESSIONS:
                oldest_session = min(game_sessions.items(), key=lambda x: x[1].get('last_activity', 0))
                del game_sessions[oldest_session[0]]
        
        if session_id not in game_sessions:
            players = [
                {"name": "플레이어1", "color": "#ff6b6b", "dice1": 0, "dice2": 0, "total": 0},
                {"name": "플레이어2", "color": "#4ecdc4", "dice1": 0, "dice2": 0, "total": 0}
            ]
            
            game_sessions[session_id] = {
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
        else:
            game_sessions[session_id]['last_activity'] = time.time()
        
        return game_sessions[session_id]

def get_game_session():
    session_id = get_session_id()
    return init_game_session(session_id)

@app.route('/')
def index():
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
            <h1>🎲 랜덤 주사위 게임</h1>
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
                    startGameLoop();
                }
            });
        }
        
        function startGameLoop() {
            gameInterval = setInterval(() => {
                fetch('/api/game_status')
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
            // 현재 플레이어 표시
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
            
            // 주사위 표시
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
            
            // 플레이어 결과 표시
            updatePlayersResults(data.players, data);
        }
        
        function updatePlayersResults(players, data) {
            const resultsContainer = document.getElementById('playersResults');
            resultsContainer.innerHTML = players.map((player, index) => {
                let className = 'player-result';
                
                // 현재 차례인 플레이어 표시
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
                
                // 승자 표시
                if (data.winner && player.name === data.winner.name) {
                    className += ' winner';
                }
                
                // 재경기 참가자 표시
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
    
    if len(game_session['players']) >= 7:
        return jsonify({'success': False, 'message': '최대 7명까지 가능합니다!'})
    
    colors = ["#ff6b6b", "#4ecdc4", "#45b7d1", "#96ceb4", "#ffeaa7", "#fd79a8", "#fdcb6e"]
    
    new_player = {
        "name": name,
        "color": colors[len(game_session['players']) % len(colors)],
        "dice1": 0,
        "dice2": 0,
        "total": 0
    }
    
    game_session['players'].append(new_player)
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
        return jsonify({'success': True})
    
    return jsonify({'success': False})

@app.route('/api/reset', methods=['POST'])
def reset_game():
    game_session = get_game_session()
    game_session['game_running'] = False
    game_session['current_player'] = 0
    game_session['dice_rolling'] = False
    game_session['game_finished'] = False
    game_session['winner'] = None
    game_session['round_number'] = 1
    game_session['tie_breaker_players'] = []
    game_session['is_tie_breaker'] = False
    
    for player in game_session['players']:
        player['dice1'] = 0
        player['dice2'] = 0
        player['total'] = 0
    
    return jsonify({'success': True})

@app.route('/api/start_game', methods=['POST'])
def start_game():
    game_session = get_game_session()
    
    if len(game_session['players']) < 2:
        return jsonify({'success': False, 'message': '최소 2명의 플레이어가 필요합니다!'})
    
    game_session['game_running'] = True
    game_session['current_player'] = 0
    game_session['dice_rolling'] = False
    game_session['game_finished'] = False
    game_session['winner'] = None
    game_session['round_number'] = 1
    game_session['tie_breaker_players'] = []
    game_session['is_tie_breaker'] = False
    
    for player in game_session['players']:
        player['dice1'] = 0
        player['dice2'] = 0
        player['total'] = 0
    
    session_id = get_session_id()
    threading.Thread(target=game_loop, args=(session_id,), daemon=True).start()
    
    return jsonify({'success': True})

@app.route('/api/game_status')
def game_status():
    game_session = get_game_session()
    return jsonify({
        'players': game_session['players'],
        'current_player': game_session['current_player'],
        'dice_rolling': game_session['dice_rolling'],
        'game_finished': game_session['game_finished'],
        'winner': game_session['winner'],
        'round_number': game_session['round_number'],
        'is_tie_breaker': game_session['is_tie_breaker'],
        'tie_breaker_players': game_session['tie_breaker_players']
    })

def game_loop(session_id):
    if session_id not in game_sessions:
        return
    
    game_session = game_sessions[session_id]
    
    while game_session['game_running'] and not game_session['game_finished']:
        # 현재 라운드에서 굴릴 플레이어들 결정
        if game_session['is_tie_breaker']:
            active_players = game_session['tie_breaker_players']
        else:
            active_players = list(range(len(game_session['players'])))
        
        current_idx = game_session['current_player']
        
        if current_idx >= len(active_players):
            # 현재 라운드의 모든 플레이어가 주사위를 굴렸음
            if game_session['is_tie_breaker']:
                # 재경기에서 승자 결정
                tie_players = [game_session['players'][i] for i in game_session['tie_breaker_players']]
                min_total = min(player['total'] for player in tie_players)
                winners = [player for player in tie_players if player['total'] == min_total]
                
                if len(winners) == 1:
                    # 단독 우승자 결정
                    game_session['winner'] = winners[0]
                    game_session['game_finished'] = True
                    break
                else:
                    # 또 동점이면 다시 재경기
                    game_session['tie_breaker_players'] = [
                        i for i, player in enumerate(game_session['players']) 
                        if player in winners
                    ]
                    game_session['current_player'] = 0
                    game_session['round_number'] += 1
                    continue
            else:
                # 첫 라운드에서 승자 결정
                min_total = min(player['total'] for player in game_session['players'])
                winners = [player for player in game_session['players'] if player['total'] == min_total]
                
                if len(winners) == 1:
                    # 단독 우승자 결정
                    game_session['winner'] = winners[0]
                    game_session['game_finished'] = True
                    break
                else:
                    # 동점이면 재경기 시작
                    game_session['tie_breaker_players'] = [
                        i for i, player in enumerate(game_session['players']) 
                        if player in winners
                    ]
                    game_session['is_tie_breaker'] = True
                    game_session['current_player'] = 0
                    game_session['round_number'] += 1
                    
                    # 재경기 플레이어들의 주사위 초기화
                    for i in game_session['tie_breaker_players']:
                        game_session['players'][i]['dice1'] = 0
                        game_session['players'][i]['dice2'] = 0
                        game_session['players'][i]['total'] = 0
                    continue
        
        # 현재 플레이어의 실제 인덱스
        actual_player_idx = active_players[current_idx]
        
        # 주사위 굴리기 시작
        game_session['dice_rolling'] = True
        time.sleep(2)  # 주사위 굴리는 연출 시간
        
        # 주사위 결과 생성
        dice1 = random.randint(1, 6)
        dice2 = random.randint(1, 6)
        total = dice1 + dice2
        
        game_session['players'][actual_player_idx]['dice1'] = dice1
        game_session['players'][actual_player_idx]['dice2'] = dice2
        game_session['players'][actual_player_idx]['total'] = total
        
        game_session['dice_rolling'] = False
        time.sleep(1)  # 결과 확인 시간
        
        game_session['current_player'] += 1

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