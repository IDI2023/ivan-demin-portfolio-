#!/usr/bin/env python3
"""Build a *lightweight* preview. CSS, JS and images are inline; MP4 remain files in assets/.
For fully functioning video, keep the preview in the extracted site folder or serve via GitHub Pages.
Do not generate unreliable 70-150MB data: MP4 URLs for iPhone embedded browsers.
"""
from pathlib import Path
from bs4 import BeautifulSoup
from base64 import b64encode
import mimetypes
root=Path(__file__).resolve().parent
soup=BeautifulSoup((root/'index.html').read_text(encoding='utf-8'),'html.parser')
for tag in list(soup.select('link[rel="stylesheet"]')):
 st=soup.new_tag('style');st.string=(root/tag['href']).read_text(encoding='utf-8');tag.replace_with(st)
for tag in list(soup.select('script[src]')):
 st=soup.new_tag('script');st.string=(root/tag['src']).read_text(encoding='utf-8');tag.decompose();soup.body.append(st)
cache={}
def inline_image(path):
 if path not in cache:
  p=root/path
  if not p.is_file():raise FileNotFoundError(p)
  mime=mimetypes.guess_type(p.name)[0] or 'image/jpeg'
  cache[path]='data:'+mime+';base64,'+b64encode(p.read_bytes()).decode('ascii')
 return cache[path]
for tag in soup.find_all(True):
 for attr in ('src','poster','href','data-poster'):
  value=tag.get(attr)
  if isinstance(value,str) and value.startswith('assets/') and Path(value).suffix.lower() in ('.jpg','.jpeg','.png','.webp','.svg'):
   tag[attr]=inline_image(value)
 if tag.has_attr('data-slides'):
  tag['data-slides']='|'.join(inline_image(x) if x.startswith('assets/') else x for x in tag['data-slides'].split('|'))
# All video src/href/data-video-src remain relative; no base64 media pseudo-player.
notice=soup.new_tag('div');notice['class']='preview-note';notice.string='Предпросмотр. Видео открываются при запуске этого HTML рядом с папкой assets из ZIP. Для просмотра с iPhone используйте сайт после публикации на GitHub Pages.'
notice_style=soup.new_tag('style');notice_style.string='.preview-note{padding:12px 18px;background:#1b1c1b;color:#fff;font:14px/1.5 sans-serif;text-align:center}'
soup.head.append(notice_style)
soup.body.insert(0,notice)
output=root/'Иван-Демин-ПРЕДПРОСМОТР.html'
output.write_text(str(soup),encoding='utf-8')
print('Light preview:',round(output.stat().st_size/1024/1024,2),'MiB', 'inlined images:',len(cache),'video: separate assets files')
