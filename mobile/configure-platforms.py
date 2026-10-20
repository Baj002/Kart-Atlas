"""Deterministic native project customization after Capacitor generates templates."""
import json,plistlib,re
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
release=json.loads((ROOT/'mobile/release.json').read_text());icon=Image.open(ROOT/'site/icon-512.png').convert('RGB')
android=ROOT/'android'
if android.exists():
    manifest=android/'app/src/main/AndroidManifest.xml'
    text=manifest.read_text().replace('<manifest xmlns:android="http://schemas.android.com/apk/res/android">','<manifest xmlns:android="http://schemas.android.com/apk/res/android" xmlns:tools="http://schemas.android.com/tools">')
    if 'tools:node="remove"' not in text:
        text=text.replace('</manifest>','<uses-permission android:name="android.permission.SCHEDULE_EXACT_ALARM" tools:node="remove"/>\n</manifest>')
    text=text.replace('android:allowBackup="true"','android:allowBackup="false"');manifest.write_text(text)
    gradle=android/'app/build.gradle';text=gradle.read_text();text=re.sub(r'versionCode \d+',f"versionCode {release['buildNumber']}",text);text=re.sub(r'versionName "[^"]+"',f"versionName \"{release['version']}\"",text);gradle.write_text(text)
    res=android/'app/src/main/res'
    for density,size in [('mdpi',48),('hdpi',72),('xhdpi',96),('xxhdpi',144),('xxxhdpi',192)]:
        directory=res/('mipmap-'+density);directory.mkdir(parents=True,exist_ok=True)
        for name in ('ic_launcher.png','ic_launcher_round.png'):icon.resize((size,size),Image.Resampling.LANCZOS).save(directory/name)
        edge=round(size*108/48);mark=round(size*66/48);foreground=Image.new('RGBA',(edge,edge),(0,0,0,0));foreground.paste(icon.resize((mark,mark)),((edge-mark)//2,(edge-mark)//2));foreground.save(directory/'ic_launcher_foreground.png')
    (res/'values/ic_launcher_background.xml').write_text('<resources><color name="ic_launcher_background">#0c1523</color></resources>')
    for splash in res.glob('*/splash.png'):
        size=Image.open(splash).size;canvas=Image.new('RGB',size,'#0c1523');edge=max(48,int(min(size)*.24));canvas.paste(icon.resize((edge,edge)),((size[0]-edge)//2,(size[1]-edge)//2));canvas.save(splash)
    drawable=res/'drawable';drawable.mkdir(exist_ok=True)
    (drawable/'ic_stat_kart.xml').write_text('<vector xmlns:android="http://schemas.android.com/apk/res/android" android:width="24dp" android:height="24dp" android:viewportWidth="24" android:viewportHeight="24"><path android:fillColor="#FFFFFFFF" android:pathData="M6,5h12l3,9H3zM3,15h18v3H3zM5,18a2,2 0,1 0,4 0a2,2 0,1 0,-4 0M15,18a2,2 0,1 0,4 0a2,2 0,1 0,-4 0"/></vector>')
ios=ROOT/'ios/App'
if ios.exists():
    project=ios/'App.xcodeproj/project.pbxproj';text=project.read_text()
    text=re.sub(r'MARKETING_VERSION = [^;]+;',f"MARKETING_VERSION = {release['version']};",text)
    text=re.sub(r'CURRENT_PROJECT_VERSION = \d+;',f"CURRENT_PROJECT_VERSION = {release['buildNumber']};",text)
    if 'PrivacyInfo.xcprivacy' not in text:
        text=text.replace('/* Begin PBXBuildFile section */','/* Begin PBXBuildFile section */\n        A11111111111111111111111 /* PrivacyInfo.xcprivacy in Resources */ = {isa = PBXBuildFile; fileRef = A22222222222222222222222; };')
        text=text.replace('/* Begin PBXFileReference section */','/* Begin PBXFileReference section */\n        A22222222222222222222222 /* PrivacyInfo.xcprivacy */ = {isa = PBXFileReference; lastKnownFileType = text.xml; path = PrivacyInfo.xcprivacy; sourceTree = "<group>"; };')
        text=text.replace('504EC3131FED79650016851F /* Info.plist */,','504EC3131FED79650016851F /* Info.plist */,\n                A22222222222222222222222 /* PrivacyInfo.xcprivacy */,')
        text=text.replace('504EC3021FED79650016851F /* Resources */ = {\n\t\t\tisa = PBXResourcesBuildPhase;', '504EC3021FED79650016851F /* Resources */ = {\n\t\t\tisa = PBXResourcesBuildPhase;')
        marker='504EC30F1FED79650016851F /* Assets.xcassets in Resources */,'
        text=text.replace(marker,marker+'\n                A11111111111111111111111 /* PrivacyInfo.xcprivacy in Resources */,')
    project.write_text(text)
    privacy={'NSPrivacyTracking':False,'NSPrivacyTrackingDomains':[],'NSPrivacyCollectedDataTypes':[], 'NSPrivacyAccessedAPITypes':[{'NSPrivacyAccessedAPIType':'NSPrivacyAccessedAPICategoryFileTimestamp','NSPrivacyAccessedAPITypeReasons':['C617.1']}]}
    (ios/'App/PrivacyInfo.xcprivacy').write_bytes(plistlib.dumps(privacy))
    plist=ios/'App/Info.plist';data=plistlib.loads(plist.read_bytes());data['ITSAppUsesNonExemptEncryption']=False;plist.write_bytes(plistlib.dumps(data))
    for splash in (ios/'App/Assets.xcassets/Splash.imageset').glob('*.png'):
        size=Image.open(splash).size;canvas=Image.new('RGB',size,'#0c1523');edge=int(min(size)*.24);canvas.paste(icon.resize((edge,edge)),((size[0]-edge)//2,(size[1]-edge)//2));canvas.save(splash)
    icon.resize((1024,1024),Image.Resampling.LANCZOS).save(ios/'App/Assets.xcassets/AppIcon.appiconset/AppIcon-512@2x.png')
print('Configured existing native projects; API 36 / iOS 15 minimum, release version, icons, and privacy manifest.')
# Store graphics are build artifacts, regenerated from the existing brand icon.
from PIL import ImageDraw,ImageFont
assets=ROOT/'build/store-assets';assets.mkdir(parents=True,exist_ok=True)
icon.save(assets/'google-play-icon-512.png');icon.resize((1024,1024),Image.Resampling.LANCZOS).save(assets/'apple-app-icon-1024.png')
canvas=Image.new('RGB',(1024,500),'#0c1523');canvas.paste(icon.resize((250,250)),(48,125));draw=ImageDraw.Draw(canvas)
font_paths=['/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf','/System/Library/Fonts/Supplemental/Arial.ttf']
def font(size):
    for path in font_paths:
        if Path(path).exists():return ImageFont.truetype(path,size)
    return ImageFont.load_default(size=size)
draw.text((336,140),'KART ATLAS',font=font(62),fill='#b3ff53')
draw.text((336,235),'Find your next kart race.',font=font(36),fill='white')
draw.text((336,305),'Race discovery · Saved races',font=font(25),fill='#cad7e4')
draw.text((336,345),'Registration deadline reminders',font=font(25),fill='#cad7e4')
canvas.save(assets/'google-play-feature-1024x500.png')
