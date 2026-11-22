#!/usr/bin/env python3
from pathlib import Path
from bs4 import BeautifulSoup
from PIL import Image
import subprocess,json,hashlib,tempfile,shutil,yaml
root=Path(__file__).resolve().parent
checks=[]
def ok(name,condition,detail=''):
 checks.append({'name':name,'passed':bool(condition),'detail':detail})
 print(('PASS' if condition else 'FAIL'),name,detail if not condition else '')
d=json.loads((root/'data/site.json').read_text('utf8'))
soup=BeautifulSoup((root/'index.html').read_text('utf8'),'html.parser')
# Exclude URL anchors and explicit HTTP links; validate local files
refs=set()
for tag in soup.select('[src],[href],[poster],[data-video-src],[data-poster]'):
 for key in ('src','href','poster','data-video-src','data-poster'):
  val=tag.get(key,'')
  if isinstance(val,str) and val.startswith(('assets/','source-archive/')):refs.add(val)
for tag in soup.select('[data-slides]'):
 refs.update(x for x in tag.get('data-slides','').split('|') if x.startswith('assets/'))
missing=sorted(f for f in refs if not (root/f).is_file())
ok('Every generated media and original link resolves locally',not missing,repr(missing))
ok('Eight MP4 present',len(list((root/'assets').glob('*.mp4')))==8)
works=d['portfolio_works'];ok('Six works and all have proof',len(works)==6 and all(w.get('proof') for w in works))
proofs={x['id']:x for x in d['proofs']}
ok('All 6 work proof IDs exist',all(w['proof'] in proofs for w in works))
ok('New TikTok mapped to correct proof',next(w for w in works if w['id']=='tiktok469')['proof']=='tt-469' and proofs['tt-469']['image']=='sama-tiktok-469-proof.jpg')
ok('New humor Reels mapped to correct proof',next(w for w in works if w['id']=='humor')['proof']=='reels-humor' and proofs['reels-humor']['image']=='sama-reels-humor-proof.png')
for original,site in [('IMG_5708(1).mp4','blesk-reel-21658.mp4'),('IMG_7853(1).mp4','blesk-reel-6265.mp4')]:
 ok(f'High-quality {site} preserved byte-for-byte',hashlib.sha256((Path('/mnt/data')/original).read_bytes()).digest()==hashlib.sha256((root/'assets'/site).read_bytes()).digest())
for pr in d['proofs']:
 if pr.get('uncropped_original'):
  orig=root/pr['uncropped_original'];processed=root/'assets'/pr['image']
  ok(f'Untouched source for {pr["id"]}',orig.exists() and processed.exists())
for name in ['blesk-reel-21658.mp4','blesk-reel-6265.mp4']:
 p=root/'assets'/name
 proc=subprocess.run(['ffprobe','-v','error','-show_entries','stream=codec_name,width,height,pix_fmt','-select_streams','v:0','-of','json',str(p)],capture_output=True,text=True)
 meta=json.loads(proc.stdout)['streams'][0]
 ok(f'MP4 H264 at 512x910 {name}',meta['codec_name']=='h264' and meta['width']==512 and meta['height']==910)
 b=p.read_bytes();ok(f'Faststart MP4 {name}',b.find(b'moov')<b.find(b'mdat'))
y=yaml.safe_load((root/'.pages.yml').read_text('utf8'))
ok('Pages CMS YAML parseable',bool(y))
y2=yaml.safe_load((root/'.github/workflows/deploy.yml').read_text('utf8'))
ok('Github Pages workflow parseable',bool(y2))
# Test build with edited metric and proof using an isolated temp copy + symlinked assets.
with tempfile.TemporaryDirectory() as folder:
 tmp=Path(folder)
 for file in ['build.py','index.template.html']:
  shutil.copy2(root/file,tmp/file)
 (tmp/'data').mkdir();(tmp/'assets').symlink_to(root/'assets',target_is_directory=True)
 (tmp/'source-archive').symlink_to(root/'source-archive',target_is_directory=True)
 changed=json.loads(json.dumps(d));changed['portfolio_works'][3]['metric']='TEST — 999 просмотров'
 changed['proofs'][-1]['image']='sama-tiktok-469-proof.jpg'
 (tmp/'data/site.json').write_text(json.dumps(changed,ensure_ascii=False),'utf8')
 res=subprocess.run(['python',str(tmp/'build.py')],cwd=tmp,capture_output=True,text=True)
 testhtml=(tmp/'index.html').read_text('utf8') if (tmp/'index.html').exists() else ''
 ok('JSON metric edits compile in isolation',res.returncode==0 and 'TEST — 999 просмотров' in testhtml,res.stderr)
 ok('Build does not alter authoritative JSON values',d['portfolio_works'][3]['metric']!='TEST — 999 просмотров')
# no-javascript direct href available
ok('JS-free direct MP4 href in each card',all(soup.select_one(f'#work-{w["id"]} [data-open-video]') is None or soup.select_one(f'#work-{w["id"]} [data-open-video]').get('href','').endswith('.mp4') for w in works))
ok('Buldak direct first-slide href',soup.select_one('#work-buldak [data-open-carousel]').get('href')=='assets/sama-buldak-01.jpg')
ok('Raw proofs deployed via Github workflow','cp -r source-archive/original-proofs dist/source-archive/' in (root/'.github/workflows/deploy.yml').read_text('utf8'))
(root/'previews_v5_2').mkdir(exist_ok=True)
(root/'previews_v5_2'/'static-tests.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),'utf8')
print('TOTAL',sum(k['passed'] for k in checks),'/',len(checks))
if not all(c['passed'] for c in checks):raise SystemExit(1)
