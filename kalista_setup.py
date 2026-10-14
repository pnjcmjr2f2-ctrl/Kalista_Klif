"""Local first-run credentials. Never publish the generated secrets or saves."""
from pathlib import Path
import secrets
import socket
import tomllib
import subprocess
import sys

root=Path(__file__).resolve().parent
config=root/'.streamlit'/'secrets.toml'
if not config.exists():
    config.parent.mkdir(exist_ok=True)
    gm=secrets.token_urlsafe(18);player=secrets.token_urlsafe(18)
    config.write_text(f'[access]\ngm_password = "{gm}"\nplayer_password = "{player}"\n',encoding='utf-8')
    config.chmod(0o600)

credentials=tomllib.loads(config.read_text(encoding='utf-8'))['access']
gm=credentials['gm_password'];player=credentials['player_password']
address='IP-компьютера'
if sys.platform == 'darwin':
    for interface in ('en0','en1'):
        result=subprocess.run(['/usr/sbin/ipconfig','getifaddr',interface],capture_output=True,text=True)
        if result.returncode==0 and result.stdout.strip():
            address=result.stdout.strip()
            break
try:
    if address=='IP-компьютера':
        with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as connection:
            connection.connect(('192.0.2.1',80));address=connection.getsockname()[0]
except OSError: pass
instructions=root/'Доступ-к-игре.txt'
instructions.write_text(f'''Калиста — доступ к игровому столу

На этом компьютере: http://127.0.0.1:8501
Телефон и компьютер должны быть в одной Wi-Fi / локальной сети.
Адрес для телефона: http://{address}:8501

Ключ ведущего: {gm}
Ключ игрока (Шеогарат): {player}

Другу передай адрес и только ключ игрока.
Ведущий видит все данные; игрок — своего персонажа и публичную сцену.
Игрок применяет свои действия напрямую и сам завершает свой ход.
Проверки очереди, ресурсов, дистанции и преград выполняются автоматически.
Боевой стол обновляется каждые 3 секунды; ведущему не нужно подтверждать атаки.
Отмена последнего изменения доступна ведущему и сохраняется после переподключения.


Ключи хранятся в .streamlit/secrets.toml. Сохрани этот файл локально.
Для смены ключей отредактируй его и перезапусти программу.
Интернет-подключение между разными сетями требует отдельного размещения
с HTTPS; локальный адрес работает только в общей сети.
''',encoding='utf-8')
instructions.chmod(0o600)
