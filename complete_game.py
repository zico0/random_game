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
                    {"name": "플레이어2", "color": "#4ecdc4", "dice1": 0, "dice2": 0, "total": 0},
                    {"name": "플레이어3", "color": "#45b7d1", "dice1": 0, "dice2": 0, "total": 0},
                    {"name": "플레이어4", "color": "#96ceb4", "dice1": 0, "dice2": 0, "total": 0}
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
            elif game_type == 'roulette':
                players = [
                    {"name": "플레이어1", "color": "#ff6b6b"},
                    {"name": "플레이어2", "color": "#4ecdc4"},
                    {"name": "플레이어3", "color": "#45b7d1"},
                    {"name": "플레이어4", "color": "#96ceb4"}
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
            elif game_type == 'horse':
                players = [
                    {"name": "말1", "color": "#FF0000", "position": 0, "speed": 0},
                    {"name": "말2", "color": "#00FF00", "position": 0, "speed": 0},
                    {"name": "말3", "color": "#0080FF", "position": 0, "speed": 0},
                    {"name": "말4", "color": "#FFFF00", "position": 0, "speed": 0}
                ]
                game_sessions[session_id] = {
                    'game_type': 'horse',
                    'players': players,
                    'game_running': False,
                    'race_started': False,
                    'game_finished': False,
                    'winner': None,
                    'winner_index': -1,
                    'game_mode': 'first',
                    'race_time': 0,
                    'last_activity': time.time()
                }
            else:  # ladder
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
                    'game_type': 'ladder',
                    'players': players,
                    'ladder_connections': [],
                    'results': results,
                    'game_running': False,
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
            grid-template-columns: repeat(2, 1fr);
            gap: 30px;
            margin: 40px 0;
            max-width: 1000px;
            margin: 40px auto;
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
        .horse-card {
            border-color: #f39c12;
            background: linear-gradient(135deg, rgba(243, 156, 18, 0.1), rgba(0,0,0,0.4));
        }
        .horse-card:hover {
            border-color: #f39c12;
            box-shadow: 0 20px 40px rgba(243, 156, 18, 0.3);
        }
        .ladder-card {
            border-color: #9b59b6;
            background: linear-gradient(135deg, rgba(155, 89, 182, 0.1), rgba(0,0,0,0.4));
        }
        .ladder-card:hover {
            border-color: #9b59b6;
            box-shadow: 0 20px 40px rgba(155, 89, 182, 0.3);
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
        @media (max-width: 900px) {
            .game-selection { grid-template-columns: 1fr; gap: 20px; }
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
            <div class="game-card horse-card" onclick="selectGame('horse')">
                <div class="game-icon">🏇</div>
                <div class="game-title">랜덤 경마 게임</div>
                <div class="game-description">
                    박진감 넘치는 경마!<br>
                    순위가 뒤바뀌는<br>
                    스릴 만점 레이스!
                </div>
            </div>
            
            <div class="game-card ladder-card" onclick="selectGame('ladder')">
                <div class="game-icon">🪜</div>
                <div class="game-title">랜덤 사다리 게임</div>
                <div class="game-description">
                    사다리를 타고 내려가서<br>
                    랜덤한 결과를<br>
                    확인하는 게임!
                </div>
            </div>
            
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
            } else if (gameType === 'horse') {
                window.location.href = '/horse';
            } else if (gameType === 'ladder') {
                window.location.href = '/ladder';
            }
        }
    </script>
</body>
</html>'''

@app.route('/dice')
def dice_game():
    # 새로운 세션 생성으로 데이터 초기화
    session_id = get_session_id()
    if session_id in game_sessions:
        del game_sessions[session_id]
    return open('dice_template.html', 'r', encoding='utf-8').read()

@app.route('/roulette')
def roulette_game():
    # 새로운 세션 생성으로 데이터 초기화
    session_id = get_session_id()
    if session_id in game_sessions:
        del game_sessions[session_id]
    return open('roulette_template.html', 'r', encoding='utf-8').read()

@app.route('/horse')
def horse_game():
    # 새로운 세션 생성으로 데이터 초기화
    session_id = get_session_id()
    if session_id in game_sessions:
        del game_sessions[session_id]
    return open('horse_template.html', 'r', encoding='utf-8').read()

@app.route('/ladder')
def ladder_game():
    # 새로운 세션 생성으로 데이터 초기화
    session_id = get_session_id()
    if session_id in game_sessions:
        del game_sessions[session_id]
    return open('ladder_template.html', 'r', encoding='utf-8').read()

# 주사위 게임 API
@app.route('/api/dice/players')
def get_dice_players():
    game_session = get_game_session('dice')
    return jsonify(game_session['players'])

@app.route('/api/dice/add_player', methods=['POST'])
def add_dice_player():
    game_session = get_game_session('dice')
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

@app.route('/api/dice/update_player', methods=['POST'])
def update_dice_player():
    game_session = get_game_session('dice')
    data = request.get_json()
    index = data.get('index')
    name = data.get('name', '').strip()
    
    if 0 <= index < len(game_session['players']) and name:
        game_session['players'][index]['name'] = name
        return jsonify({'success': True})
    
    return jsonify({'success': False})

@app.route('/api/dice/remove_player', methods=['POST'])
def remove_dice_player():
    game_session = get_game_session('dice')
    data = request.get_json()
    index = data.get('index')
    
    if len(game_session['players']) <= 2:
        return jsonify({'success': False, 'message': '최소 2명의 플레이어가 필요합니다!'})
    
    if 0 <= index < len(game_session['players']):
        game_session['players'].pop(index)
        return jsonify({'success': True})
    
    return jsonify({'success': False})

@app.route('/api/dice/reset', methods=['POST'])
def reset_dice_game():
    game_session = get_game_session('dice')
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

@app.route('/api/dice/start_game', methods=['POST'])
def start_dice_game():
    game_session = get_game_session('dice')
    
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
    threading.Thread(target=dice_game_loop, args=(session_id,), daemon=True).start()
    
    return jsonify({'success': True})

@app.route('/api/dice/game_status')
def dice_game_status():
    game_session = get_game_session('dice')
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

# 룰렛 게임 API
@app.route('/api/roulette/players')
def get_roulette_players():
    game_session = get_game_session('roulette')
    return jsonify(game_session['players'])

@app.route('/api/roulette/add_player', methods=['POST'])
def add_roulette_player():
    game_session = get_game_session('roulette')
    data = request.get_json()
    name = data.get('name', '').strip()
    
    if not name:
        return jsonify({'success': False, 'message': '이름을 입력하세요!'})
    
    if len(game_session['players']) >= 10:
        return jsonify({'success': False, 'message': '최대 10명까지 가능합니다!'})
    
    colors = ["#FF0000", "#00FF00", "#0080FF", "#FFFF00", "#FF8000", "#FF00FF", "#00FFFF", "#8000FF", "#FF0080", "#80FF00"]
    
    new_player = {
        "name": name,
        "color": colors[len(game_session['players']) % len(colors)]
    }
    
    game_session['players'].append(new_player)
    return jsonify({'success': True})

@app.route('/api/roulette/update_player', methods=['POST'])
def update_roulette_player():
    game_session = get_game_session('roulette')
    data = request.get_json()
    index = data.get('index')
    name = data.get('name', '').strip()
    
    if 0 <= index < len(game_session['players']) and name:
        game_session['players'][index]['name'] = name
        return jsonify({'success': True})
    
    return jsonify({'success': False})

@app.route('/api/roulette/remove_player', methods=['POST'])
def remove_roulette_player():
    game_session = get_game_session('roulette')
    data = request.get_json()
    index = data.get('index')
    
    if len(game_session['players']) <= 2:
        return jsonify({'success': False, 'message': '최소 2명의 플레이어가 필요합니다!'})
    
    if 0 <= index < len(game_session['players']):
        game_session['players'].pop(index)
        return jsonify({'success': True})
    
    return jsonify({'success': False})

@app.route('/api/roulette/reset', methods=['POST'])
def reset_roulette_game():
    game_session = get_game_session('roulette')
    game_session['game_running'] = False
    game_session['roulette_spinning'] = False
    game_session['game_finished'] = False
    game_session['winner'] = None
    game_session['winner_index'] = -1
    game_session['spin_angle'] = 0
    
    return jsonify({'success': True})

@app.route('/api/roulette/start_game', methods=['POST'])
def start_roulette_game():
    game_session = get_game_session('roulette')
    
    if len(game_session['players']) < 2:
        return jsonify({'success': False, 'message': '최소 2명의 플레이어가 필요합니다!'})
    
    game_session['game_running'] = True
    game_session['roulette_spinning'] = False
    game_session['game_finished'] = False
    game_session['winner'] = None
    game_session['winner_index'] = -1
    game_session['spin_angle'] = 0
    
    session_id = get_session_id()
    threading.Thread(target=roulette_game_loop, args=(session_id,), daemon=True).start()
    
    return jsonify({'success': True})

@app.route('/api/roulette/game_status')
def roulette_game_status():
    game_session = get_game_session('roulette')
    return jsonify({
        'players': game_session['players'],
        'roulette_spinning': game_session['roulette_spinning'],
        'game_finished': game_session['game_finished'],
        'winner': game_session['winner'],
        'winner_index': game_session['winner_index'],
        'spin_angle': game_session['spin_angle']
    })

def dice_game_loop(session_id):
    if session_id not in game_sessions:
        return
    
    game_session = game_sessions[session_id]
    
    while game_session['game_running'] and not game_session['game_finished']:
        if game_session['is_tie_breaker']:
            active_players = game_session['tie_breaker_players']
        else:
            active_players = list(range(len(game_session['players'])))
        
        current_idx = game_session['current_player']
        
        if current_idx >= len(active_players):
            if game_session['is_tie_breaker']:
                tie_players = [game_session['players'][i] for i in game_session['tie_breaker_players']]
                min_total = min(player['total'] for player in tie_players)
                winners = [player for player in tie_players if player['total'] == min_total]
                
                if len(winners) == 1:
                    game_session['winner'] = winners[0]
                    game_session['game_finished'] = True
                    break
                else:
                    game_session['tie_breaker_players'] = [
                        i for i, player in enumerate(game_session['players']) 
                        if player in winners
                    ]
                    game_session['current_player'] = 0
                    game_session['round_number'] += 1
                    continue
            else:
                min_total = min(player['total'] for player in game_session['players'])
                winners = [player for player in game_session['players'] if player['total'] == min_total]
                
                if len(winners) == 1:
                    game_session['winner'] = winners[0]
                    game_session['game_finished'] = True
                    break
                else:
                    game_session['tie_breaker_players'] = [
                        i for i, player in enumerate(game_session['players']) 
                        if player in winners
                    ]
                    game_session['is_tie_breaker'] = True
                    game_session['current_player'] = 0
                    game_session['round_number'] += 1
                    
                    for i in game_session['tie_breaker_players']:
                        game_session['players'][i]['dice1'] = 0
                        game_session['players'][i]['dice2'] = 0
                        game_session['players'][i]['total'] = 0
                    continue
        
        actual_player_idx = active_players[current_idx]
        
        game_session['dice_rolling'] = True
        time.sleep(2)
        
        dice1 = random.randint(1, 6)
        dice2 = random.randint(1, 6)
        total = dice1 + dice2
        
        game_session['players'][actual_player_idx]['dice1'] = dice1
        game_session['players'][actual_player_idx]['dice2'] = dice2
        game_session['players'][actual_player_idx]['total'] = total
        
        game_session['dice_rolling'] = False
        time.sleep(1)
        
        game_session['current_player'] += 1

def roulette_game_loop(session_id):
    if session_id not in game_sessions:
        return
    
    game_session = game_sessions[session_id]
    
    # 3초 대기 후 시작 (카운트다운 시간)
    time.sleep(3.5)
    
    game_session['roulette_spinning'] = True
    
    # 더 긴 스핀 시간으로 긴장감 조성
    spin_duration = 5.0
    start_time = time.time()
    
    # 더 많은 회전으로 박진감 증대
    final_angle = random.randint(2160, 3600)  # 6-10바퀴
    
    while time.time() - start_time < spin_duration:
        current_time = time.time() - start_time
        progress = current_time / spin_duration
        
        # 더 부드러운 감속 곡선으로 긴장감 조성
        if progress < 0.7:
            # 처음 70%는 빠르게
            eased_progress = progress * 0.8
        else:
            # 마지막 30%에서 급격히 감속
            remaining = (progress - 0.7) / 0.3
            eased_progress = 0.56 + (1 - 0.56) * (1 - (1 - remaining) ** 4)
        
        game_session['spin_angle'] = final_angle * eased_progress
        
        # 스핀 속도에 따른 업데이트 간격 조정
        if progress < 0.5:
            time.sleep(0.03)  # 빠른 구간
        else:
            time.sleep(0.08)  # 느린 구간
    
    game_session['spin_angle'] = final_angle
    game_session['roulette_spinning'] = False
    
    # 정확한 세그먼트 계산
    segment_angle = 360 / len(game_session['players'])
    normalized_angle = (360 - (final_angle % 360)) % 360
    winner_index = int(normalized_angle / segment_angle)
    
    if winner_index >= len(game_session['players']):
        winner_index = 0
    
    game_session['winner_index'] = winner_index
    game_session['winner'] = game_session['players'][winner_index]
    
    # 결과 발표 전 잠시 대기
    time.sleep(1.0)
    game_session['game_finished'] = True

# 경마 게임 API
@app.route('/api/horse/players')
def get_horse_players():
    game_session = get_game_session('horse')
    return jsonify(game_session['players'])

@app.route('/api/horse/add_player', methods=['POST'])
def add_horse_player():
    game_session = get_game_session('horse')
    data = request.get_json()
    name = data.get('name', '').strip()
    
    if not name:
        return jsonify({'success': False, 'message': '이름을 입력하세요!'})
    
    if len(game_session['players']) >= 10:
        return jsonify({'success': False, 'message': '최대 10마리까지 가능합니다!'})
    
    colors = ["#FF0000", "#00FF00", "#0080FF", "#FFFF00", "#FF8000", "#FF00FF", "#00FFFF", "#8000FF", "#FF0080", "#80FF00"]
    
    new_player = {
        "name": name,
        "color": colors[len(game_session['players']) % len(colors)],
        "position": 0,
        "speed": 0
    }
    
    game_session['players'].append(new_player)
    return jsonify({'success': True})

@app.route('/api/horse/update_player', methods=['POST'])
def update_horse_player():
    game_session = get_game_session('horse')
    data = request.get_json()
    index = data.get('index')
    name = data.get('name', '').strip()
    
    if 0 <= index < len(game_session['players']) and name:
        game_session['players'][index]['name'] = name
        return jsonify({'success': True})
    
    return jsonify({'success': False})

@app.route('/api/horse/remove_player', methods=['POST'])
def remove_horse_player():
    game_session = get_game_session('horse')
    data = request.get_json()
    index = data.get('index')
    
    if len(game_session['players']) <= 2:
        return jsonify({'success': False, 'message': '최소 2마리가 필요합니다!'})
    
    if 0 <= index < len(game_session['players']):
        game_session['players'].pop(index)
        return jsonify({'success': True})
    
    return jsonify({'success': False})

@app.route('/api/horse/set_mode', methods=['POST'])
def set_horse_mode():
    game_session = get_game_session('horse')
    data = request.get_json()
    mode = data.get('mode')
    
    if mode in ['first', 'last']:
        game_session['game_mode'] = mode
        return jsonify({'success': True})
    
    return jsonify({'success': False})

@app.route('/api/horse/reset', methods=['POST'])
def reset_horse_game():
    game_session = get_game_session('horse')
    game_session['game_running'] = False
    game_session['race_started'] = False
    game_session['game_finished'] = False
    game_session['winner'] = None
    game_session['winner_index'] = -1
    game_session['race_time'] = 0
    
    for player in game_session['players']:
        player['position'] = 0
        player['speed'] = 0
    
    return jsonify({'success': True})

@app.route('/api/horse/start_game', methods=['POST'])
def start_horse_game():
    game_session = get_game_session('horse')
    
    if len(game_session['players']) < 2:
        return jsonify({'success': False, 'message': '최소 2마리가 필요합니다!'})
    
    # 완전한 게임 상태 초기화
    game_session['game_running'] = True
    game_session['race_started'] = False
    game_session['game_finished'] = False
    game_session['winner'] = None
    game_session['winner_index'] = -1
    game_session['race_time'] = 0
    
    # 모든 플레이어 데이터 완전 초기화
    for player in game_session['players']:
        player['position'] = 0
        player['speed'] = 0
    
    session_id = get_session_id()
    threading.Thread(target=horse_race_loop, args=(session_id,), daemon=True).start()
    
    return jsonify({'success': True})

@app.route('/api/horse/game_status')
def horse_game_status():
    game_session = get_game_session('horse')
    return jsonify({
        'players': game_session['players'],
        'race_started': game_session['race_started'],
        'game_finished': game_session['game_finished'],
        'winner': game_session['winner'],
        'winner_index': game_session['winner_index'],
        'game_mode': game_session['game_mode'],
        'race_time': game_session['race_time']
    })

def horse_race_loop(session_id):
    if session_id not in game_sessions:
        return
    
    game_session = game_sessions[session_id]
    
    # 카운트다운
    time.sleep(3.5)
    game_session['race_started'] = True
    
    race_distance = 100
    start_time = time.time()
    finish_times = {}  # 각 말의 결승선 도달 시간 기록
    
    while game_session['game_running'] and not game_session['game_finished']:
        current_time = time.time()
        game_session['race_time'] = current_time - start_time
        
        # 각 말의 속도와 위치 업데이트
        for i, player in enumerate(game_session['players']):
            # 랜덤한 속도 변화로 박진감 연출
            speed_change = random.uniform(-0.8, 1.5)
            player['speed'] = max(0.2, min(2.5, player['speed'] + speed_change))
            
            # 위치 업데이트
            player['position'] += player['speed'] * 0.3
            
            # 결승선 도달 시 시간 기록 및 위치 고정
            if player['position'] >= race_distance and i not in finish_times:
                finish_times[i] = current_time - start_time
                player['position'] = race_distance
        
        # 모든 말이 결승선에 도달했는지 체크
        if len(finish_times) == len(game_session['players']):
            if game_session['game_mode'] == 'first':
                # 1등 모드: 가장 빨리 도달한 말
                winner_idx = min(finish_times.keys(), key=lambda x: finish_times[x])
            else:
                # 꼴등 모드: 가장 늦게 도달한 말
                winner_idx = max(finish_times.keys(), key=lambda x: finish_times[x])
            
            game_session['winner'] = game_session['players'][winner_idx]
            game_session['winner_index'] = winner_idx
            game_session['game_finished'] = True
            break
        
        time.sleep(0.1)

# 사다리 게임 API
@app.route('/api/ladder/players')
def get_ladder_players():
    game_session = get_game_session('ladder')
    return jsonify(game_session['players'])

@app.route('/api/ladder/add_player', methods=['POST'])
def add_ladder_player():
    game_session = get_game_session('ladder')
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

@app.route('/api/ladder/update_player', methods=['POST'])
def update_ladder_player():
    game_session = get_game_session('ladder')
    data = request.get_json()
    index = data.get('index')
    name = data.get('name', '').strip()
    
    if 0 <= index < len(game_session['players']) and name:
        game_session['players'][index]['name'] = name
        return jsonify({'success': True})
    
    return jsonify({'success': False})

@app.route('/api/ladder/remove_player', methods=['POST'])
def remove_ladder_player():
    game_session = get_game_session('ladder')
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

@app.route('/api/ladder/reset', methods=['POST'])
def reset_ladder_game():
    game_session = get_game_session('ladder')
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

@app.route('/api/ladder/preview_results')
def ladder_preview_results():
    game_session = get_game_session('ladder')
    return jsonify({'results': game_session['results']})

@app.route('/api/ladder/start_game', methods=['POST'])
def start_ladder_game():
    game_session = get_game_session('ladder')
    
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
    threading.Thread(target=ladder_game_loop, args=(session_id,), daemon=True).start()
    
    return jsonify({'success': True, 'ladder_connections': game_session['ladder_connections'], 'results': game_session['results']})

@app.route('/api/ladder/game_status')
def ladder_game_status():
    game_session = get_game_session('ladder')
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

def ladder_game_loop(session_id):
    if session_id not in game_sessions:
        return
    
    game_session = game_sessions[session_id]
    finish_line = 102
    
    update_interval = 0.15
    while game_session['game_running']:
        try:
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
                        break
            
            if not game_session['game_running']:
                break
                
            time.sleep(update_interval)
        except Exception:
            game_session['game_running'] = False
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