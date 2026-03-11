import json
import urllib.request
import os

# Configuration variables
URL = "https://content-download-egs.distro.on.epicgames.com/iOS/altstore/source.json"
APPS_JSON = "apps.json"
VER_TXT = "epic-ver.txt"
TARGETS = ["com.epicgames.FortniteGame", "uk.co.mediatonic.fallguys"]

# Allowed keys schema
ALLOWED_APP_KEYS = {"name", "bundleIdentifier", "developerName", "subtitle", "version", "versionDate", "versionDescription", "size", "minOSVersion", "downloadURL", "localizedDescription", "iconURL", "tintColor", "screenshotURLs", "versions", "beta", "category", "appPermissions"}
ALLOWED_VERSION_KEYS = {"version", "date", "localizedDescription", "downloadURL", "size", "minOSVersion"}

# Fetch Epic source
req = urllib.request.Request(URL, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as response:
    epic_data = json.loads(response.read().decode('utf-8'))

# Load local repo
if os.path.exists(APPS_JSON):
    with open(APPS_JSON, 'r', encoding='utf-8') as f:
        my_data = json.load(f)
else:
    my_data = {"apps": []}

new_versions = {}

# Process target apps
for epic_app in epic_data.get("apps", []):
    bundle_id = epic_app.get("bundleIdentifier")
    
    if bundle_id in TARGETS:
        # Enforce English description
        if "_localizedDescriptions" in epic_app and "en" in epic_app["_localizedDescriptions"]:
            epic_app["localizedDescription"] = epic_app["_localizedDescriptions"]["en"]

        # Filter root keys
        clean_app = {k: v for k, v in epic_app.items() if k in ALLOWED_APP_KEYS}
        
        # Process latest version and extract IPA from manifest
        if "versions" in clean_app and len(clean_app["versions"]) > 0:
            v0 = clean_app["versions"][0]
            clean_v0 = {k: v for k, v in v0.items() if k in ALLOWED_VERSION_KEYS}
            
            if "date" in clean_v0:
                clean_v0["date"] = clean_v0["date"].split("T")[0]
            
            if "downloadURL" in clean_v0:
                base_url = clean_v0["downloadURL"]
                if not base_url.endswith('/'):
                    base_url += '/'
                try:
                    m_req = urllib.request.Request(base_url + "manifest.json", headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(m_req) as m_res:
                        m_data = json.loads(m_res.read().decode('utf-8'))
                        variants = m_data.get("variants", [])
                        if variants and "assetPath" in variants[0]:
                            clean_v0["downloadURL"] = base_url + variants[0]["assetPath"]
                except Exception:
                    pass
            
            clean_app["versions"] = [clean_v0]
            new_versions[bundle_id] = clean_v0.get("version", "unknown")
            
            # Sync root attributes with version
            clean_app["version"] = clean_v0.get("version", clean_app.get("version"))
            clean_app["versionDate"] = clean_v0.get("date", clean_app.get("versionDate"))
            if "size" in clean_v0: clean_app["size"] = clean_v0["size"]
            if "downloadURL" in clean_v0: clean_app["downloadURL"] = clean_v0["downloadURL"]
            if "minOSVersion" in clean_v0: clean_app["minOSVersion"] = clean_v0["minOSVersion"]
        
        # Merge with local data
        found = False
        for i, my_app in enumerate(my_data.get("apps", [])):
            if my_app.get("bundleIdentifier") == bundle_id:
                clean_app["name"] = my_app.get("name", clean_app.get("name"))
                clean_app["subtitle"] = my_app.get("subtitle", clean_app.get("subtitle"))
                my_data["apps"][i] = clean_app
                found = True
                break
                
        if not found:
            my_data["apps"].append(clean_app)

# Save repo
with open(APPS_JSON, 'w', encoding='utf-8') as f:
    json.dump(my_data, f, indent=2, ensure_ascii=False)

# Save versions
with open(VER_TXT, 'w', encoding='utf-8') as f:
    for b_id, ver in new_versions.items():
        f.write(f"{b_id}: {ver}\n")