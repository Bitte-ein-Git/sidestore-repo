import json
import urllib.request
import os

URL = "https://github.com/LiveContainer/LiveContainer/releases/download/1.0/apps_ss_lc.json"
APPS_JSON = "apps.json"
TARGET_BUNDLE = "com.kdt.livecontainer"

# Define strictly allowed keys based on existing schema
ALLOWED_APP_KEYS = {"name", "bundleIdentifier", "developerName", "subtitle", "version", "versionDate", "versionDescription", "size", "minOSVersion", "downloadURL", "localizedDescription", "iconURL", "tintColor", "screenshotURLs", "versions", "beta", "category", "appPermissions"}
ALLOWED_VERSION_KEYS = {"version", "date", "localizedDescription", "downloadURL", "size", "minOSVersion"}

req = urllib.request.Request(URL, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as response:
    lc_data = json.loads(response.read().decode('utf-8'))

if os.path.exists(APPS_JSON):
    with open(APPS_JSON, 'r', encoding='utf-8') as f:
        my_data = json.load(f)
else:
    my_data = {"apps": []}

for remote_app in lc_data.get("apps", []):
    if remote_app.get("bundleIdentifier") == TARGET_BUNDLE:
        # Filter root app dictionary
        clean_app = {k: v for k, v in remote_app.items() if k in ALLOWED_APP_KEYS}
        
        # Process and filter newest version
        if "versions" in clean_app and len(clean_app["versions"]) > 0:
            v0 = clean_app["versions"][0]
            clean_v0 = {k: v for k, v in v0.items() if k in ALLOWED_VERSION_KEYS}
            
            # Format date to YYYY-MM-DD
            if "date" in clean_v0:
                clean_v0["date"] = clean_v0["date"].split("T")[0]
            
            clean_app["versions"] = [clean_v0]
            
            # Sync root attributes with latest version
            clean_app["version"] = clean_v0.get("version", clean_app.get("version"))
            clean_app["versionDate"] = clean_v0.get("date", clean_app.get("versionDate"))
            if "size" in clean_v0: clean_app["size"] = clean_v0["size"]
            if "downloadURL" in clean_v0: clean_app["downloadURL"] = clean_v0["downloadURL"]
            if "minOSVersion" in clean_v0: clean_app["minOSVersion"] = clean_v0["minOSVersion"]

        # Merge with existing data
        found = False
        for i, my_app in enumerate(my_data.get("apps", [])):
            if my_app.get("bundleIdentifier") == TARGET_BUNDLE:
                # Preserve local overrides
                clean_app["name"] = my_app.get("name", clean_app.get("name"))
                clean_app["subtitle"] = my_app.get("subtitle", clean_app.get("subtitle"))
                clean_app["iconURL"] = my_app.get("iconURL", clean_app.get("iconURL")) # Preserve local iconURL
                
                my_data["apps"][i] = clean_app
                found = True
                break
                
        if not found:
            my_data["apps"].append(clean_app)
        break

with open(APPS_JSON, 'w', encoding='utf-8') as f:
    json.dump(my_data, f, indent=2, ensure_ascii=False)