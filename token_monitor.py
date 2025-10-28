import requests
import time
from datetime import datetime
import json
import os

WEBHOOK_URL = "https://discord.com/api/webhooks/1432537921189052436/pIVaQuJHjIBeX2ZRTO1mvm3YDP6rCPtgD5_PrLtgSO7hZywK47F0D-BbEX7UsGn8_qjl"
API_URL = "https://dev.fun/api/home.listProjects"
POLL_INTERVAL = 10

seen_ids = set()

def get_projects():
    try:
        params = {
            "input": json.dumps({
                "json": {
                    "limit": 21,
                    "search": "",
                    "sortBy": "created_on",
                    "sortOrder": "desc",
                    "type": "all",
                    "direction": "forward"
                }
            })
        }
        response = requests.get(API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        items = data.get("result", {}).get("data", {}).get("json", {}).get("items", [])
        return items
    except Exception as e:
        print(f"Error: {e}")
        return []

def send_notification(project):
    try:
        token_info = project.get("token")
        has_token = token_info is not None
        description = project.get("oneliner", project.get("description", "No description"))[:500]
        
        embed = {
            "title": f"NEW TOKEN ALERT: {project.get('name', 'Unknown')}",
            "description": description,
            "color": 65280,
            "timestamp": datetime.utcnow().isoformat(),
            "fields": []
        }
        
        if has_token:
            token_name = token_info.get("name", "")
            token_symbol = token_info.get("symbol", "")
            marketcap = token_info.get("marketcap", 0)
            embed["title"] = f"NEW TOKEN: {project.get('name', 'Unknown')} ({token_symbol})"
            
            embed["fields"].append({
                "name": "Token Info",
                "value": f"{token_name} ({token_symbol})\nMarket Cap: ${marketcap:,.2f}",
                "inline": False
            })
            
            contract = token_info.get("contractAddress", "")
            embed["fields"].append({
                "name": "Contract",
                "value": contract,
                "inline": True
            })
            
            pump_url = token_info.get("website", "")
            if pump_url:
                embed["fields"].append({
                    "name": "Links",
                    "value": f"[View on pump.fun]({pump_url})",
                    "inline": False
                })
        
        user_info = project.get("user", {})
        creator = user_info.get("username") or user_info.get("displayName", "Unknown")
        embed["fields"].append({
            "name": "Created By",
            "value": creator,
            "inline": True
        })
        
        created_at = project.get("createdAt", "")
        if created_at:
            embed["fields"].append({
                "name": "Created",
                "value": created_at[:10],
                "inline": True
            })
        
        payload = {"embeds": [embed]}
        response = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        return response.status_code == 204
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def monitor():
    print("="*60)
    print("DEV.FUN TOKEN MONITOR - CLOUD DEPLOYMENT")
    print(f"Polling every {POLL_INTERVAL} seconds...")
    print("="*60)
    print()
    
    initial_projects = get_projects()
    for project in initial_projects:
        if project.get("id"):
            seen_ids.add(project.get("id"))
    print(f"Initial load: {len(initial_projects)} projects tracked. Monitoring...")
    print()
    
    while True:
        try:
            projects = get_projects()
            new_projects = []
            
            for project in projects:
                project_id = project.get("id")
                if project_id and project_id not in seen_ids:
                    new_projects.append(project)
                    seen_ids.add(project_id)
            
            if new_projects:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] *** NEW TOKEN DETECTED ***")
                for project in new_projects:
                    send_notification(project)
                    print(f"Sent notification: {project.get('name', 'Unknown')}")
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Monitoring...")
                
        except Exception as e:
            print(f"Error: {e}")
        
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    monitor()
