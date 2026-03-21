import os,json,logging,urllib.request
from dotenv import load_dotenv
load_dotenv()

TELEGRAM_BOT_TOKEN=os.getenv("TITAN_BOT_TOKEN","")
TELEGRAM_CHAT_ID=os.getenv("TELEGRAM_CHAT_ID","")
GEMINI_API_KEY=os.getenv("GEMINI_API_KEY","")
ANTHROPIC_API_KEY=os.getenv("ANTHROPIC_API_KEY","")
OLLAMA_URL="http://localhost:11434/api/generate"
OLLAMA_MODEL="llama3.2"
GEMINI_MODEL="gemini-2.5-flash-preview-04-17"
HAIKU_MODEL="claude-haiku-4-5-20251001"

logging.basicConfig(level=logging.INFO,format="%(asctime)s [TITAN] %(message)s",handlers=[logging.StreamHandler(),logging.FileHandler("titan.log",encoding="utf-8")])
logger=logging.getLogger("titan")

def llama_call(prompt,system=""):
    try:
        payload=json.dumps({"model":OLLAMA_MODEL,"prompt":f"{system}\n\n{prompt}" if system else prompt,"stream":False,"options":{"temperature":0.3,"num_predict":500}}).encode()
        req=urllib.request.Request(OLLAMA_URL,data=payload,headers={"Content-Type":"application/json"})
        with urllib.request.urlopen(req,timeout=60) as r:
            return json.loads(r.read().decode()).get("response","").strip()
    except Exception as e:
        logger.error(f"Llama failed: {e}")
        return ""

def gemini_call(prompt,system=""):
    try:
        if not GEMINI_API_KEY: return llama_call(prompt,system)
        url=f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
        contents=[]
        if system:
            contents.append({"role":"user","parts":[{"text":system}]})
            contents.append({"role":"model","parts":[{"text":"Understood."}]})
        contents.append({"role":"user","parts":[{"text":prompt}]})
        payload=json.dumps({"contents":contents}).encode()
        req=urllib.request.Request(url,data=payload,headers={"Content-Type":"application/json"})
        with urllib.request.urlopen(req,timeout=30) as r:
            return json.loads(r.read().decode())["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        logger.error(f"Gemini failed: {e}")
        return llama_call(prompt,system)

def haiku_call(prompt,system=""):
    try:
        if not ANTHROPIC_API_KEY: return gemini_call(prompt,system)
        payload=json.dumps({"model":HAIKU_MODEL,"max_tokens":1000,"system":system or "You are Titan, investment agent.","messages":[{"role":"user","content":prompt}]}).encode()
        req=urllib.request.Request("https://api.anthropic.com/v1/messages",data=payload,headers={"x-api-key":ANTHROPIC_API_KEY,"anthropic-version":"2023-06-01","Content-Type":"application/json"})
        with urllib.request.urlopen(req,timeout=30) as r:
            return json.loads(r.read().decode())["content"][0]["text"].strip()
    except Exception as e:
        logger.error(f"Haiku failed: {e}")
        return gemini_call(prompt,system)

TASK_CATEGORIES={"drive":["google drive","drive","organize files","folder","document"],"gmail":["gmail","email","inbox","mail","unread"],"investment":["stock","portfolio","trade","buy","sell","kiwoom"],"research":["find","search","compare","best","research"],"general":[]}

def route_task(message):
    msg=message.lower()
    for cat,kws in TASK_CATEGORIES.items():
        if any(k in msg for k in kws): return cat
    r=llama_call(f"Classify into one: drive,gmail,investment,research,general\nTask: {message}\nOne word only.")
    return r.strip().lower() if r.strip().lower() in TASK_CATEGORIES else "general"

def select_model(cat):
    if cat=="investment": return "haiku"
    elif cat in ("drive","gmail","research"): return "gemini"
    return "llama"

SYSTEMS={"drive":"You are Titan, Google Drive organizer. Propose clean folder structure. Wait for GO before executing.","gmail":"You are Titan, Gmail organizer. Categories: Important,Finance,Work,Personal,Newsletters,Archive,Delete. Propose first, execute on GO.","investment":"You are Titan, investment agent. Propose specific trades with exact prices. NEVER execute without GO from GOD.","research":"You are Titan, research agent. Find best options, compare objectively, give clear recommendation.","general":"You are Titan, personal AI agent. Execute tasks autonomously. Report results clearly."}

def execute_task(message,cat,model):
    sys=SYSTEMS.get(cat,SYSTEMS["general"])
    if model=="haiku": return haiku_call(message,sys)
    elif model=="gemini": return gemini_call(message,sys)
    return llama_call(message,sys)

pending={}

def send_tg(text,chat_id=None):
    try:
        cid=chat_id or TELEGRAM_CHAT_ID
        url=f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload=json.dumps({"chat_id":cid,"text":text,"parse_mode":"HTML"}).encode()
        req=urllib.request.Request(url,data=payload,headers={"Content-Type":"application/json"})
        with urllib.request.urlopen(req,timeout=10) as r:
            return json.loads(r.read().decode()).get("ok",False)
    except Exception as e:
        logger.error(f"TG failed: {e}")
        return False

def get_updates(offset=0):
    try:
        url=f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?offset={offset}&timeout=30"
        req=urllib.request.Request(url,headers={"User-Agent":"TitanAgent/1.0"})
        with urllib.request.urlopen(req,timeout=35) as r:
            return json.loads(r.read().decode()).get("result",[])
    except Exception as e:
        logger.error(f"Updates failed: {e}")
        return []

def handle(msg):
    try:
        cid=str(msg["chat"]["id"])
        text=msg.get("text","").strip()
        if not text: return
        logger.info(f"MSG: {text[:80]}")
        if text.upper() in ("GO","EXECUTE","CONFIRM"):
            if cid in pending:
                a=pending.pop(cid)
                send_tg("⚡ Executing...",cid)
                r=execute_task(f"GOD approved. Execute now.\nRequest:{a['task']}\nPlan:{a['plan']}\nProvide final result.",a["cat"],a["model"])
                send_tg(f"✅ Done\n\n{r}",cid)
            else:
                send_tg("No pending task.",cid)
            return
        if text.upper() in ("CANCEL","NO","STOP"):
            pending.pop(cid,None)
            send_tg("❌ Cancelled.",cid)
            return
        send_tg(f"⚡ Received: {text[:80]}\nAnalyzing...",cid)
        cat=route_task(text)
        model=select_model(cat)
        plan=execute_task(text,cat,model)
        if not plan:
            send_tg("⚠️ Analysis failed. Try again.",cid)
            return
        pending[cid]={"task":text,"plan":plan,"cat":cat,"model":model}
        send_tg(f"🎯 TITAN PLAN\nType:{cat.upper()} Brain:{model.upper()}\n\n{plan}\n\nReply GO to execute or CANCEL.",cid)
    except Exception as e:
        logger.error(f"Handle failed: {e}",exc_info=True)

def main():
    logger.info("⚡ TITAN STARTING")
    send_tg("⚡ TITAN ONLINE\nPersonal autonomous agent ready.\n\nSend any task:\n- Organize Google Drive\n- Sort Gmail\n- Research best X\n- Analyze portfolio\n\nI plan then you say GO then I execute.")
    offset=0
    while True:
        try:
            updates=get_updates(offset)
            for u in updates:
                offset=u["update_id"]+1
                if "message" in u: handle(u["message"])
        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(f"Loop error: {e}")
            import time; time.sleep(5)

if __name__=="__main__":
    main()