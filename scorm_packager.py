#!/usr/bin/env python3
import os, zipfile, shutil, sys, tempfile
from pathlib import Path

SRC = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
OUT = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else (SRC.parent / "GoToMarket_SCORM12.zip")

# --- helpers ---
def find_entry_html(root: Path):
    candidates = []
    for dp, _, files in os.walk(root):
        for f in files:
            if f.lower().endswith(".html"):
                p = Path(dp) / f
                score = 100
                name = f.lower()
                if name == "index.html": score -= 80
                if "home" in name: score -= 50
                if "accueil" in name: score -= 40
                depth = len(Path(dp).relative_to(root).parts)
                score += depth * 5
                candidates.append((score, p))
    candidates.sort(key=lambda x: x[0])
    return candidates[0][1] if candidates else None

def write_launch_html(path: Path, entry_rel: str):
    api_wrapper_js = r"""
var scorm=(function(){var api=null,isConnected=false;
function findAPI(win){var max=500;while((!win.API)&&(win.parent&&win.parent!=win)&&max>0){max--;win=win.parent}return win.API||null}
function getAPI(){if(api!==null)return api;api=findAPI(window)||(window.opener?findAPI(window.opener):null);return api}
function init(){try{var a=getAPI();if(!a){console.warn("SCORM API not found");return false}
var res=a.LMSInitialize("");isConnected=(res+"")==="true";if(!isConnected)console.warn("LMSInitialize failed");
var status=a.LMSGetValue("cmi.core.lesson_status");if(!status||status==="not attempted"){a.LMSSetValue("cmi.core.lesson_status","incomplete");a.LMSCommit("")}
return isConnected}catch(e){console.error(e);return false}}
function complete(){try{var a=getAPI();if(!a||!isConnected)return;a.LMSSetValue("cmi.core.lesson_status","completed");a.LMSCommit("")}catch(e){console.error(e)}}
function quit(){try{var a=getAPI();if(!a||!isConnected)return;a.LMSFinish("")}catch(e){console.error(e)}}
return{init:init,complete:complete,quit:quit}})();
window.addEventListener("load",function(){scorm.init()});
window.addEventListener("beforeunload",function(){scorm.complete();scorm.quit()});
"""
    html = f"""<!doctype html>
<html lang="fr"><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>GoToMarket – SCORM Launch</title>
<style>html,body{{height:100%;margin:0}}.frame{{width:100%;height:100%;border:0}}
.fallback{{padding:1rem;font-family:system-ui,sans-serif}}.notice{{background:#fff3cd;border:1px solid #ffeeba;padding:.75rem;margin-bottom:1rem}}</style>
</head><body>
<div class="fallback"><div class="notice">Module empaqueté au format SCORM 1.2.</div></div>
<iframe class="frame" src="{entry_rel}" title="GoToMarket"></iframe>
<script>{api_wrapper_js}</script>
</body></html>"""
    path.write_text(html, encoding="utf-8")

def write_manifest(path: Path):
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<manifest identifier="MANIFEST-GoToMarket" version="1.0"
  xmlns="http://www.imsproject.org/xsd/imscp_rootv1p1p2"
  xmlns:adlcp="http://www.adlnet.org/xsd/adlcp_rootv1p2"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="
    http://www.imsproject.org/xsd/imscp_rootv1p1p2 imscp_rootv1p1p2.xsd
    http://www.adlnet.org/xsd/adlcp_rootv1p2 adlcp_rootv1p2.xsd
  ">
  <metadata><schema>ADL SCORM</schema><schemaversion>1.2</schemaversion></metadata>
  <organizations default="ORG-GoToMarket">
    <organization identifier="ORG-GoToMarket" structure="hierarchical">
      <title>GoToMarket</title>
      <item identifier="ITEM-GoToMarket" identifierref="RES-GoToMarket" isvisible="true">
        <title>GoToMarket</title>
      </item>
    </organization>
  </organizations>
  <resources>
    <resource identifier="RES-GoToMarket" type="webcontent" adlcp:scormtype="sco" href="launch.html">
      <file href="launch.html"/>
    </resource>
  </resources>
</manifest>"""
    path.write_text(xml, encoding="utf-8")

def zip_dir(src: Path, out_zip: Path):
    if out_zip.exists(): out_zip.unlink()
    with zipfile.ZipFile(out_zip, 'w', zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(src):
            for f in files:
                full = Path(root)/f
                rel = str(full.relative_to(src))
                z.write(full, rel)

# --- build in a safe temp dir (avoid recursion) ---
tmp_root = Path(tempfile.mkdtemp(prefix="scorm_build_"))
BUILD = tmp_root
COURSE = BUILD / "course"
COURSE.mkdir(parents=True, exist_ok=True)

# Copy SRC into /course, ignoring self-build and bulky dirs
ignore = shutil.ignore_patterns(
    "_scorm_build*", "scorm_build_*", ".git", ".git*", "__pycache__", "node_modules", "node_modules/*", ".DS_Store"
)
shutil.copytree(SRC, COURSE, dirs_exist_ok=True, ignore=ignore)

# Detect entry HTML (inside course)
entry = find_entry_html(COURSE)
entry_rel = entry.relative_to(BUILD).as_posix() if entry else "course/"

# Create launch + manifest at BUILD root
write_launch_html(BUILD/"launch.html", entry_rel)
write_manifest(BUILD/"imsmanifest.xml")

# Zip BUILD -> OUT
zip_dir(BUILD, OUT)
print(f"[OK] SCORM 1.2 créé : {OUT}")
print(f"[INFO] Dossier de build temporaire : {BUILD}")