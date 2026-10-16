"""Local, user-started SSH tunnel launcher; only forwards Kalista's HTTP port."""
from pathlib import Path
import json,os,re,signal,subprocess,sys,time,urllib.request
ROOT=Path(__file__).resolve().parent
RUN=ROOT.parent/'work'/'tunnel';RUN.mkdir(parents=True,exist_ok=True)
STATE=RUN/'online.json';LINK=ROOT/'Онлайн-доступ.txt'
PYTHON=ROOT.parent/'work'/'venv'/'bin'/'python'

def alive(pid):
    try:os.kill(pid,0);return True
    except (ProcessLookupError,PermissionError):return False

def status():
    try:return json.loads(STATE.read_text())
    except (OSError,ValueError):return {}

def health():
    try:return urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health',timeout=2).status==200
    except OSError:return False

def worker():
    if not health():
        log=(RUN/'app.log').open('a')
        subprocess.Popen([str(PYTHON),'-m','streamlit','run','kalista_app.py','--server.address','0.0.0.0','--server.port','8501','--server.headless','true','--server.showEmailPrompt','false','--browser.gatherUsageStats','false'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        for _ in range(30):
            if health():break
            time.sleep(1)
        if not health():raise RuntimeError('Приложение не запустилось: смотри work/tunnel/app.log')
    command=['ssh','-F','/dev/null','-T','-o','ConnectTimeout=15','-o','ServerAliveInterval=20','-o','ServerAliveCountMax=3','-o','ExitOnForwardFailure=yes','-o','StrictHostKeyChecking=accept-new','-o','UserKnownHostsFile='+str(RUN/'known_hosts'),'-o','IdentityAgent=none','-o','IdentitiesOnly=yes','-o','IdentityFile=/dev/null','-R','80:127.0.0.1:8501','nokey@localhost.run']
    process=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
    sleep_guard=subprocess.Popen(['/usr/bin/caffeinate','-i','-w',str(os.getpid())])
    state=dict(pid=os.getpid(),ssh_pid=process.pid,url='');STATE.write_text(json.dumps(state))
    def stop(*_):
        process.terminate();sleep_guard.terminate();raise SystemExit(0)
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
    try:
        with (RUN/'online.log').open('a') as log:
            for line in process.stdout:
                log.write(line);log.flush()
                match=re.search(r'https://[a-zA-Z0-9.-]+\.(?:lhr\.life|lhr\.rocks)',line)
                if match:
                    state['url']=match[0];STATE.write_text(json.dumps(state))
                    LINK.write_text('Калиста — временная онлайн-ссылка\n\n'+match[0]+'\n\nВход по прежним ключам. Другу передавайте только ключ игрока.\nКомпьютер и VPN должны работать. Не закрывайте крышку ноутбука.\nАдрес может измениться после повторного запуска или отключения сервиса.\nОстановить внешний доступ: Остановить-онлайн.command.\n')
                    LINK.chmod(0o600)
        process.wait()
    finally:
        sleep_guard.terminate();STATE.unlink(missing_ok=True)
        LINK.write_text('Туннель остановлен. Для новой ссылки запустите Запустить-онлайн.command.\n')

def main():
    action=sys.argv[1] if len(sys.argv)>1 else 'start'
    if action=='worker':worker();return
    old=status()
    if action=='stop':
        if old.get('pid') and alive(old['pid']):os.kill(old['pid'],signal.SIGTERM)
        print('Внешний доступ остановлен. Локальная игра продолжает работать.');return
    if not old.get('pid') or not alive(old['pid']):
        with (RUN/'launcher.log').open('a') as log:subprocess.Popen([str(PYTHON),str(Path(__file__).resolve()),'worker'],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    for _ in range(45):
        current=status()
        if current.get('url') and alive(current['pid']):print('Онлайн-ссылка: '+current['url']);return
        time.sleep(1)
    raise SystemExit('Ссылка пока не получена. Логи: work/tunnel/online.log и launcher.log')
if __name__=='__main__':main()
