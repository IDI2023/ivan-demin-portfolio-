#!/usr/bin/env python3
import json, subprocess, re, sys, hashlib, os
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
root=Path(__file__).parent
results=[]
def chk(label, ok, detail=''):
 results.append({'name':label,'passed':bool(ok),'detail':str(detail)[:260]});print(('PASS' if ok else 'FAIL'),label,detail if not ok else '')
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
 page=browser.new_page(viewport={'width':390,'height':844},device_scale_factor=1,is_mobile=True,has_touch=True)
 exceptions=[]; page.on('pageerror',lambda e:exceptions.append(str(e)))
 page.set_content((root/'Иван-Демин-ПРЕДПРОСМОТР.html').read_text('utf8'),wait_until='domcontentloaded')
 chk('Autonomous markup loads',bool(page.locator('.gallery-card').count()))
 chk('6 works / 8 video files',page.locator('.gallery-card').count()==6 and len(list((root/'assets').glob('*.mp4')))==8)
 chk('Proof links in all 6 works',all(page.locator('.gallery-card').nth(i).locator('a.gallery-proof').count()==1 for i in range(6)))
 for width in [320,375,390,430,768,1024,1440]:
  page.set_viewport_size({'width':width,'height':844})
  page.wait_for_timeout(170)
  delta=page.evaluate('document.documentElement.scrollWidth - window.innerWidth')
  chk(f'No horizontal overflow {width}px',delta<=1,delta)
 page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(300)
 (root/'previews_v5_2').mkdir(exist_ok=True)
 page.screenshot(path=str(root/'previews_v5_2'/'mobile-first.png'),full_page=False)
 page.locator('#portfolio').scroll_into_view_if_needed();page.wait_for_timeout(550);page.screenshot(path=str(root/'previews_v5_2'/'mobile-gallery.png'))
 page.locator('#blesk').scroll_into_view_if_needed();page.wait_for_timeout(550);page.screenshot(path=str(root/'previews_v5_2'/'mobile-blesk.png'))
 # video modal (unloaded until triggered)
 for i in [0,1,3,4,5]:
  card=page.locator('.gallery-card').nth(i)
  src=card.locator('[data-open-video]').get_attribute('href')
  card.locator('[data-open-video]').click();page.wait_for_timeout(300)
  dialog=page.locator('#work-video-dialog')
  chk(f'Open local video #{i+1}',dialog.evaluate('(el)=>el.open') and src in page.locator('#work-player').get_attribute('src'),src)
  chk(f'Direct MP4 fallback #{i+1}',src==page.locator('#work-video-external').get_attribute('href'))
  dialog.locator('.dialog-close').click();page.wait_for_timeout(80)
  chk(f'Close local video #{i+1}',not dialog.evaluate('(el)=>el.open'))
 # carousel
 carousel=page.locator('.gallery-card').nth(2).locator('[data-open-carousel]');carousel.click()
 chk('Buldak opens',page.locator('#work-carousel-dialog').evaluate('(el)=>el.open'))
 for n in range(2,6):
  page.locator('#work-carousel-dialog [data-move="1"]').click()
  chk(f'Buldak slide {n}',page.locator('#slide-counter').inner_text()==f'{n} / 5')
 chk('Buldak fallback image direct',page.locator('#gallery-slide-external').get_attribute('href')==page.locator('#gallery-slide').get_attribute('src'))
 page.locator('#work-carousel-dialog .dialog-close').click()
 # each gallery proof
 for i in range(6):
  link=page.locator('.gallery-card').nth(i).locator('.gallery-proof');target=link.get_attribute('href')
  link.click();page.wait_for_timeout(70)
  chk(f'Proof matches card {i+1}',page.evaluate('location.hash')==target and page.locator(target).is_visible(),target)
  page.locator(f'{target} .proof-close').click();page.wait_for_timeout(60)
 # survey + nested raw images
 page.locator('.survey-result-link').click();page.wait_for_timeout(80)
 page.locator('#proof-survey summary').click()
 for n in (1,2):
  page.locator(f'#proof-survey a[href="#proof-traffic-{n}"]').click();page.wait_for_timeout(65)
  chk(f'Open survey original {n}',page.evaluate('location.hash')==f'#proof-traffic-{n}')
  page.locator(f'#proof-traffic-{n} .proof-close').click();page.wait_for_timeout(80)
  chk(f'Return from original {n} to table',page.evaluate('location.hash')=='#proof-survey')
 page.locator('#proof-survey .proof-close').click();page.wait_for_timeout(80)
 chk('Survey returns focus to opener',page.evaluate("document.activeElement.classList.contains('survey-result-link')"))
 chk('JS errors absent',len(exceptions)==0,exceptions)
 # bot video
 bot=page.locator('.bot-watch');bot.click();page.wait_for_timeout(100)
 chk('VK bot modal opens',page.locator('#work-video-dialog').evaluate('(el)=>el.open'))
 page.locator('#work-video-dialog .dialog-close').click()
 # desktop screenshots
 page.set_viewport_size({'width':1440,'height':900});page.set_content((root/'Иван-Демин-ПРЕДПРОСМОТР.html').read_text('utf8'),wait_until='domcontentloaded');page.screenshot(path=str(root/'previews_v5_2'/'desktop-first.png'))
 page.locator('#portfolio').scroll_into_view_if_needed();page.wait_for_timeout(550);page.screenshot(path=str(root/'previews_v5_2'/'desktop-gallery.png'))
 browser.close()
(root/'previews_v5_2'/'qa-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),'utf8')
print('TOTAL',sum(x['passed'] for x in results),'/',len(results))
if not all(x['passed'] for x in results):sys.exit(1)
