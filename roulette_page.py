@app.route('/roulette')
def roulette_game():
    return '''<!DOCTYPE html>
<html>
<head>
    <title>🎡 랜덤 룰렛 게임</title>
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
            background: #ff6b6b;
            color: white;
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
            .roulette-area { padding: 20px 10px; }
            .roulette-container { width: 250px; height: 250px; }
            .container { padding: 8px; }
            .setup-panel { padding: 12px; }
            .game-area { padding: 8px; min-height: 90vh; max-width: 100%; }
            .header h1 { font-size: 2em; }
        }
        @media (max-width: 480px) {
            .input-group { gap: 5px; }
            .input-group input { font-size: 13px; padding: 8px; }
            .btn { padding: 8px 12px; font-size: 13px; }
            .roulette-container { width: 200px; height: 200px; }
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
            border: 2px solid #ff6b6b;
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
        .btn-primary { background: #ff6b6b; color: white; }
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
        .roulette-area {
            background: rgba(0,0,0,0.3);
            border-radius: 15px;
            padding: 30px;
            margin: 20px 0;
            text-align: center;
        }
        .roulette-status {
            font-size: 1.5em;
            margin-bottom: 20px;
            color: #ff6b6b;
        }
        .roulette-container {
            position: relative;
            width: 300px;
            height: 300px;
            margin: 30px auto;
        }
        .roulette-wheel {
            width: 100%;
            height: 100%;
            border-radius: 50%;
            position: relative;
            border: 8px solid #333;
            box-shadow: 0 0 30px rgba(255, 107, 107, 0.5);
            transition: transform 3s cubic-bezier(0.25, 0.1, 0.25, 1);
        }
        .roulette-wheel.spinning {
            transition: transform 3s cubic-bezier(0.25, 0.1, 0.25, 1);
        }
        .roulette-segment {
            position: absolute;
            width: 50%;
            height: 50%;
            transform-origin: 100% 100%;
            overflow: hidden;
        }
        .roulette-segment-inner {
            width: 200%;
            height: 200%;
            border-radius: 50%;
            transform: rotate(45deg);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            color: white;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.8);
            font-size: 12px;
        }
        .roulette-pointer {
            position: absolute;
            top: -15px;
            left: 50%;
            transform: translateX(-50%);
            width: 0;
            height: 0;
            border-left: 15px solid transparent;
            border-right: 15px solid transparent;
            border-top: 30px solid #ffd700;
            z-index: 10;
            filter: drop-shadow(0 2px 4px rgba(0,0,0,0.5));
        }
        .roulette-center {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 40px;
            height: 40px;
            background: linear-gradient(45deg, #333, #666);
            border-radius: 50%;
            border: 3px solid #ffd700;
            z-index: 5;
        }
        .players-list {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .player-item {
            background: rgba(0,0,0,0.3);
            padding: 15px;
            border-radius: 15px;
            text-align: center;
            border: 2px solid transparent;
        }
        .player-item.winner {
            border-color: #2ecc71;
            background: rgba(46, 204, 113, 0.2);
            box-shadow: 0 0 15px rgba(46, 204, 113, 0.5);
        }
        .player-item-name {
            font-size: 1.1em;
            font-weight: bold;
            margin-bottom: 5px;
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
            <h1>🎡 랜덤 룰렛 게임</h1>
            <p>플레이어를 설정하고 시작 버튼을 눌러 룰렛을 돌리세요!</p>
        </div>
        
        <div class="setup-panel" id="setupPanel">
            <div class="input-group">
                <input type="text" id="playerName" placeholder="플레이어 이름 입력" maxlength="15">
                <button class="btn btn-primary" onclick="addPlayer()">추가</button>
            </div>
            
            <div class="players-grid" id="playersGrid"></div>
            
            <div class="controls">
                <button class="btn btn-success" onclick="startGame()">🎡 시작</button>
                <button class="btn btn-danger" onclick="resetGame()">🔄 리셋</button>
            </div>
        </div>
        
        <div class="game-area" id="gameArea">
            <div class="roulette-area">
                <div class="roulette-status" id="rouletteStatus">룰렛을 돌리는 중...</div>
                <div class="roulette-container">
                    <div class="roulette-pointer"></div>
                    <div class="roulette-wheel" id="rouletteWheel"></div>
                    <div class="roulette-center"></div>
                </div>
            </div>
            
            <div class="players-list" id="playersList"></div>
            
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
            fetch('/api/roulette/players')
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
            
            if (currentPlayers.length >= 10) {
                alert('최대 10명까지만 추가할 수 있습니다!');
                return;
            }
            
            fetch('/api/roulette/add_player', {
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
            
            fetch('/api/roulette/update_player', {
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
            fetch('/api/roulette/remove_player', {
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
            fetch('/api/roulette/reset', {method: 'POST'})
            .then(() => loadPlayers());
        }
        
        function startGame() {
            if (currentPlayers.length < 2) {
                alert('최소 2명의 플레이어가 필요합니다!');
                return;
            }
            
            fetch('/api/roulette/start_game', {method: 'POST'})
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('setupPanel').style.display = 'none';
                    document.getElementById('gameArea').style.display = 'block';
                    setupRoulette();
                    startGameLoop();
                }
            });
        }
        
        function setupRoulette() {
            const wheel = document.getElementById('rouletteWheel');
            const playersList = document.getElementById('playersList');
            
            // 룰렛 휠 생성
            wheel.innerHTML = '';
            const segmentAngle = 360 / currentPlayers.length;
            
            currentPlayers.forEach((player, index) => {
                const segment = document.createElement('div');
                segment.className = 'roulette-segment';
                segment.style.transform = `rotate(${index * segmentAngle}deg)`;
                
                const segmentInner = document.createElement('div');
                segmentInner.className = 'roulette-segment-inner';
                segmentInner.style.background = player.color;
                segmentInner.textContent = player.name;
                
                segment.appendChild(segmentInner);
                wheel.appendChild(segment);
            });
            
            // 플레이어 목록 생성
            playersList.innerHTML = currentPlayers.map((player, index) => 
                `<div class="player-item" id="player-${index}">
                    <div class="player-item-name" style="color: ${player.color};">${player.name}</div>
                </div>`
            ).join('');
        }
        
        function startGameLoop() {
            gameInterval = setInterval(() => {
                fetch('/api/roulette/game_status')
                .then(response => response.json())
                .then(data => {
                    updateGameDisplay(data);
                    
                    if (data.game_finished) {
                        clearInterval(gameInterval);
                        setTimeout(() => {
                            showWinner(data.winner);
                        }, 1000);
                    }
                });
            }, 100);
        }
        
        function updateGameDisplay(data) {
            const wheel = document.getElementById('rouletteWheel');
            const status = document.getElementById('rouletteStatus');
            
            if (data.roulette_spinning) {
                status.textContent = '룰렛을 돌리는 중...';
                wheel.style.transform = `rotate(${data.spin_angle}deg)`;
                wheel.classList.add('spinning');
            } else if (data.game_finished) {
                status.textContent = `${data.winner.name} 당첨!`;
                wheel.classList.remove('spinning');
                
                // 당첨자 하이라이트
                document.querySelectorAll('.player-item').forEach((item, index) => {
                    if (index === data.winner_index) {
                        item.classList.add('winner');
                    }
                });
            }
        }
        
        function showWinner(winner) {
            document.getElementById('winnerText').textContent = `${winner.name} 당첨!`;
            document.getElementById('winnerDetails').textContent = '🎡 룰렛이 선택했습니다!';
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
            fetch('/api/roulette/reset', {method: 'POST'})
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