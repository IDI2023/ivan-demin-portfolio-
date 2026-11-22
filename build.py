#!/usr/bin/env python3
"""Build a portable portfolio from data/site.json + index.template.html. Python stdlib only.
Original screenshots are never rewritten; video derivatives are generated once in assets/.
"""
from html import escape
from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parent
d=json.loads((ROOT/'data/site.json').read_text(encoding='utf-8'))
def h(x):return escape(str(x),quote=True)
def asset(filename):
 if not filename or '/' in filename or '\\' in filename or '..' in filename:raise ValueError('Invalid media file '+repr(filename))
 if not (ROOT/'assets'/filename).is_file():raise FileNotFoundError('Missing asset: '+filename)
 return 'assets/'+h(filename)
# One editable data source for screenshots, metrics and gallery work.
proofs=d.get('proofs', [])
proof_ids=set()
for proof in proofs:
 slug=proof.get('id','')
 if not re.fullmatch(r'[a-z0-9-]+', slug):raise ValueError('Invalid proof ID: '+repr(slug))
 if slug in proof_ids:raise ValueError('Duplicate proof ID '+slug)
 proof_ids.add(slug)
 asset(proof['image'])
 close_to=proof.get('return_to','')
 if not re.fullmatch(r'#[A-Za-z0-9_-]+', close_to):raise ValueError('Invalid return_to '+repr(close_to))
def proof_link(proof_id):
 if proof_id not in proof_ids:raise ValueError('No proof with ID '+repr(proof_id))
 return '#proof-'+h(proof_id)
def proof_anchors(links):
 return ''.join(f'<a href="{proof_link(item["proof"])}">{h(item["label"])}</a>' for item in links)
def sama_metrics():
 out=['<div class="sama-metrics" id="sama-metrics">']
 for metric in d.get('sama_metrics',[]):
  value=h(metric['value']).replace('→','<i>→</i>')
  period=f'<small class="metric-period">{h(metric["period"])}</small>' if metric.get('period') else ''
  out.append(f'<div class="metric"><span class="metric-head">{h(metric["label"])}</span>'
             f'<strong>{value}</strong>{period}<div class="metric-links">{proof_anchors(metric.get("links",[]))}</div></div>')
 out.append('</div>')
 return ''.join(out)
def sama_period():
 m=d['sama_period_metric']
 return (f'<div class="period-note period-stat"><span class="metric-head">{h(m["label"])}</span>'
         f'<div class="period-stat-line"><strong>{h(m["value"])}</strong><span>{h(m["description"])}</span></div>'
         f'<a href="{proof_link(m["proof"])}">{h(m["proof_label"])}</a></div>')
def blesk_reels():
 parts=['<div class="videos-grid">']
 for m in d.get('blesk_reels',[]):
  video=asset(m['video']); poster=asset(m['poster'])
  facts=''.join(f'<span>{h(x)}</span>' for x in m.get('facts',[]))
  parts.append(f'<article class="video-card"><video aria-label="{h(m["alt"])}" controls height="910" playsinline '
               f'poster="{poster}" preload="metadata" src="{video}" width="512"></video>'
               f'<div class="video-text"><span class="eyebrow">{h(m["label"])}</span>'
               f'<strong>{h(m["views"])}</strong><p>{h(m["views_label"])}</p>'
               f'<div class="video-submetrics">{facts}</div>'
               f'<a class="proof-link" href="{proof_link(m["proof"])}">{h(m["proof_label"])} <span aria-hidden="true">↗</span></a>'
               '</div></article>')
 return ''.join(parts)+'</div>'
def survey_values():
 rows=d.get('survey_sources',[])
 total=sum(int(r['count']) for r in rows)
 social=sum(int(r['count']) for r in rows if r.get('role')=='social')
 returning=sum(int(r['count']) for r in rows if r.get('role')=='repeat')
 others=total-returning
 if total<=0 or others<=0 or not social:raise ValueError('Survey counts/groups are invalid')
 percent_all=f'{social/total*100:.1f}'.replace('.',',')
 percent_others=f'{social/others*100:.1f}'.replace('.',',')
 fmt=lambda n: f'{n:,}'.replace(',',' ')
 platform=' · '.join(f'{r["name"]} — {fmt(int(r["count"]))}' for r in rows if r.get('role')=='social')
 template=d.get('sama_survey_summary','')
 for key,val in {'total':fmt(total),'social':fmt(social),'total_pct':percent_all}.items():
  template=template.replace('{'+key+'}',val)
 if re.search(r'{[A-Za-z_]+}',template):raise ValueError('Unknown survey placeholder in sama_survey_summary')
 return {'total':fmt(total),'social':fmt(social),'nonrepeat':fmt(others),'all_pct':percent_all,
         'other_pct':percent_others,'summary':template,'platform':platform}
survey=survey_values()
def survey_table():
 rows=d.get('survey_sources',[])
 total=sum(int(r['count']) for r in rows)
 table='<table class="survey-table"><thead><tr><th scope="col">Источник</th><th scope="col">Ответов</th></tr></thead><tbody>'
 table+=''.join(f'<tr><td>{h(r["name"])}</td><td>{h(r["count"])}</td></tr>' for r in rows)
 return table+f'<tr class="survey-table-total"><th scope="row">Всего</th><td>{total:,}</td></tr></tbody></table>'.replace('1,171','1 171')
def survey_modal():
 return ('<section class="proof-modal survey-proof-modal" id="proof-survey" role="dialog" aria-modal="true" aria-labelledby="survey-modal-title" tabindex="-1">'
         '<div class="proof-top"><span id="survey-modal-title">Источники знакомства с раменной · опрос посетителей</span><div class="proof-top-actions">'
         '<a class="proof-close" href="#traffic" aria-label="Закрыть результаты опроса">Закрыть ×</a></div></div>'
         '<a class="proof-backdrop" href="#traffic" tabindex="-1" aria-label="Закрыть просмотр"></a>'
         f'<div class="survey-modal-body"><h3>Результаты опроса</h3><p>{h(survey["total"])} ответов посетителей. Instagram и TikTok указали {h(survey["social"])} человек.</p>'
         + survey_table() + '<details class="survey-originals"><summary>Оригинальные таблицы</summary>'
         '<a href="#proof-traffic-1">Исходный скриншот · часть 1 ↗</a>'
         '<a href="#proof-traffic-2">Исходный скриншот · часть 2 ↗</a>'
         '</details></div></section>')

def proof_modals():
 """One clean public screenshot viewer; untouched sources remain in the archive.

 Uncropped originals are validated, but never linked from the public lightbox.
 """
 out=[]
 for proof in proofs:
  slug,label,filename,close_to=(proof[x] for x in ('id','label','image','return_to'))
  public_image=asset(filename)
  raw=proof.get('uncropped_original','')
  if raw:
   if (not raw.startswith('source-archive/original-proofs/') or '..' in raw
       or not (ROOT/raw).is_file()):
    raise ValueError('Invalid original source file '+repr(raw))
  out.append(f'<section class="proof-modal" id="proof-{h(slug)}" role="dialog" aria-modal="true" aria-label="{h(label)}" tabindex="-1">'
             f'<div class="proof-top"><span>{h(label)}</span><div class="proof-top-actions">'
             f'<a class="proof-close" href="{h(close_to)}" aria-label="Закрыть просмотр">Закрыть ×</a>'
             '</div></div>'
             f'<a class="proof-backdrop" href="{h(close_to)}" tabindex="-1" aria-label="Закрыть просмотр"></a>'
             f'<img src="{public_image}" alt="{h(label)}" loading="lazy"></section>')
 return '\n'.join(out)+ '\n' + survey_modal()
def bot_metrics():
 stats=[x for x in d.get('bot_stats',[]) if x.get('value') and x.get('label')]
 if not stats:return ''
 return '<div class="bot-metrics">'+''.join(f'<div><strong>{h(x["value"])}</strong><span>{h(x["label"])}</span></div>' for x in stats)+'</div>'
def portfolio_gallery():
 out=[]
 for idx,item in enumerate(d.get('portfolio_works',[])):
  kind=item['type'];poster=asset(item['poster']);title=h(item['title']);metric=h(item['metric'])
  platform=h(item['platform']);desc=h(item.get('desc',''));slug=h(item['id']);proof=item.get('proof','')
  if kind=='video':
   video=asset(item['video'])
   primary=f'<a class="gallery-play" href="{video}" data-open-video data-video-src="{video}" data-poster="{poster}" data-title="{title}" aria-label="Смотреть видео: {title}"><span aria-hidden="true">▶</span> Смотреть видео</a>'
  elif kind=='carousel':
   slides=[asset(x) for x in item['slides']]
   if len(slides)!=5:raise ValueError('Expected five carousel slides')
   primary=f'<a class="gallery-play" href="{slides[0]}" data-open-carousel data-slides="{h("|".join(slides))}" data-title="{title}" aria-label="Листать карусель {title}"><span aria-hidden="true">▣</span> Листать 5 слайдов</a>'
  else:raise ValueError('Invalid work type')
  proof_button=(f'<a class="gallery-proof" href="{proof_link(proof)}">Статистика ↗</a>' if proof else '')
  out.append(f'<article class="gallery-card" id="work-{slug}">'
     f'<div class="gallery-cover"><img src="{poster}" alt="Обложка работы: {title}" loading="lazy" decoding="async" width="512" height="910">'
     f'<span class="gallery-index">{idx+1:02} / {platform}</span></div>'
     f'<div class="gallery-copy"><h3>{title}</h3><p class="gallery-description">{desc}</p>'
     f'<p class="gallery-stat">{metric}</p><div class="gallery-actions">{primary}{proof_button}</div></div></article>')
 return '\n'.join(out)
def buldak_fallback():
 """One collapsed no-JS fallback below the card grid, not affecting card heights."""
 carousels=[work for work in d.get('portfolio_works',[]) if work.get('type')=='carousel']
 if not carousels:return ''
 slides=[asset(path) for path in carousels[0]['slides']]
 return ('<details class="gallery-slide-fallback"><summary>Если карусель не открывается — слайды отдельно</summary><div>'
         + ''.join(f'<a href="{url}" target="_blank" rel="noopener noreferrer">Слайд {idx} ↗</a>' for idx,url in enumerate(slides,1))
         + '</div></details>')
html=(ROOT/'index.template.html').read_text(encoding='utf-8')
subs={
 'telegram':re.sub('[^A-Za-z0-9_]','',d.get('telegram','')),
 'hero_title':h(d['hero_title']),'hero_desc':h(d['hero_desc']),
 'work_intro':h(d['work_intro']),'sama_intro':h(d['sama_intro']),
 'sama_approach':h(d['sama_approach']),
 'blesk_intro':h(d['blesk_intro']),'blesk_audience':h(d['blesk_audience']),
 'bot_intro':h(d['bot_intro']),'bot_video_intro':h(d['bot_video_intro']),
 'skills_intro':h(d['skills_intro']),'contact_intro':h(d['contact_intro']),
 'projects_heading_first':h(d['projects_heading_first']),
 'projects_heading_second':h(d['projects_heading_second']),
 'owner_title_first':h(d['owner_title_first']),
 'owner_title_em':h(d['owner_title_em']),
 'owner_description':h(d['owner_description']),
 'portfolio_heading_first':h(d['portfolio_heading_first']),
 'portfolio_heading_em':h(d['portfolio_heading_em']),
 'portfolio_heading_last':h(d['portfolio_heading_last']),
 'portfolio_description':h(d['portfolio_description']),
 'sama_metrics_html':sama_metrics(), 'sama_period_html':sama_period(),
 'blesk_reels_html':blesk_reels(),
 'survey_pct_norepeat':h(survey['other_pct']),
 'survey_accessible_summary':h(survey['social']+' из '+survey['nonrepeat']+' ответов, если исключить категорию «Уже были у нас», назвали Instagram или TikTok'),
 'survey_count_nonrepeat':h(survey['social']+' из '+survey['nonrepeat']+' ответа'),
 'survey_platform_counts':h(survey['platform']),
 'survey_summary':h(survey['summary']),
 'bot_before':asset(d['bot_media']['before']),
 'bot_after':asset(d['bot_media']['after']),
 'bot_video':asset(d['bot_media']['video']),
 'portfolio_gallery_html':portfolio_gallery(), 'buldak_fallback_html':buldak_fallback(),
 'proof_modals':proof_modals(),'bot_stats_html':bot_metrics()
}
for k,v in subs.items():html=html.replace('[['+k+']]',v)
missing=re.findall(r'\[\[[a-z_]+\]\]',html)
if missing:raise ValueError('Unbound fields: '+str(missing))
for proof in proofs:
 if proof['return_to'].startswith('#proof-') and proof['return_to'][7:] not in proof_ids and proof['return_to']!='#proof-survey':
  raise ValueError('Invalid return_to proof target '+proof['return_to'])
# Optional asset replacements make all base-case photos/videos editable from JSON.
for original,replacement in d.get('asset_aliases',{}).items():
    if original == replacement:continue
    old='assets/'+original
    new=asset(replacement)
    html=html.replace('"'+old+'"','"'+new+'"')
(ROOT/'index.html').write_text(html,encoding='utf-8')
print('Built index.html',len(html),'bytes;',len(d['portfolio_works']),'works')
