/* Progressive enhancements: published original links and hash proof images work without JavaScript. */
(() => {
  const nav = document.querySelector('.nav-mobile');
  if (nav) nav.querySelectorAll('nav a').forEach(a => a.addEventListener('click', () => {nav.open = false;}));

  // Hash viewers work without JS. With JS, keep a separate opener for the
  // survey and each nested original so focus returns to the right level.
  const proofSelector = '.proof-modal:target';
  let proofTrigger = null;
  let surveyImageTrigger = null;
  let previousProofId = null;
  document.querySelectorAll('a[href^="#proof-"]').forEach(link => {
    link.addEventListener('click', () => {
      if (link.matches('.proof-close, .proof-backdrop')) return;
      const container = link.closest('.proof-modal');
      if (container?.id === 'proof-survey' && /^#proof-traffic-[12]$/.test(link.getAttribute('href'))) {
        surveyImageTrigger = link;
      } else if (!container) {
        proofTrigger = link;
        surveyImageTrigger = null;
      }
    });
  });
  const background = [...document.body.children].filter(node =>
    node.matches?.('main, header, .skip-link, .media-dialog'));
  function proofState() {
    const current = document.querySelector(proofSelector);
    const returningToSurvey = current?.id === 'proof-survey' &&
      ['proof-traffic-1','proof-traffic-2'].includes(previousProofId);
    background.forEach(node => { node.inert = !!current; });
    document.querySelectorAll('.proof-modal').forEach(node => {
      const inactive = node !== current;
      node.inert = inactive;
      if (inactive) node.setAttribute('aria-hidden', 'true');
      else node.removeAttribute('aria-hidden');
    });
    if (current) {
      const focusTarget = returningToSurvey && surveyImageTrigger?.isConnected
        ? surveyImageTrigger : current.querySelector('.proof-close');
      focusTarget?.focus({preventScroll: true});
    } else if (proofTrigger?.isConnected) {
      proofTrigger.focus({preventScroll: true});
      proofTrigger = null;
      surveyImageTrigger = null;
    }
    previousProofId = current?.id || null;
  }
  window.addEventListener('hashchange', proofState);
  if (location.hash.startsWith('#proof-')) proofState();
  document.addEventListener('keydown', e => {
    const proof = document.querySelector(proofSelector);
    if (proof && e.key === 'Tab') {
      const targets = [...proof.querySelectorAll('a[href]:not([tabindex="-1"]),button:not([disabled]),summary')]
        .filter(node => node.getClientRects().length && !node.closest('details:not([open])'));
      if (targets.length) {
        const index = targets.indexOf(document.activeElement);
        if (e.shiftKey && index <= 0) {
          e.preventDefault(); targets[targets.length - 1].focus();
        } else if (!e.shiftKey && (index === targets.length - 1 || index === -1)) {
          e.preventDefault(); targets[0].focus();
        }
      }
    }
    if (e.key === 'Escape') {
      if (proof) { e.preventDefault(); proof.querySelector('.proof-close')?.click(); }
      if (nav?.open) nav.open = false;
    }
  });

  const videoDialog=document.getElementById('work-video-dialog');
  const player=document.getElementById('work-player');
  const videoHeading=document.getElementById('work-video-heading');
  const videoKicker=videoDialog?.querySelector('.dialog-kicker');
  const videoExternal=document.getElementById('work-video-external');
  const videoLoadError=document.getElementById('video-load-error');
  const galleryDialog=document.getElementById('work-carousel-dialog');
  const slide=document.getElementById('gallery-slide');
  const slideCounter=document.getElementById('slide-counter');
  const slideExternal=document.getElementById('gallery-slide-external');
  let videoTrigger=null, carouselTrigger=null,slides=[],active=0;
  function openNative(dialog){
    if(!dialog || typeof dialog.showModal !== 'function')return false;
    try{ dialog.showModal(); dialog.querySelector('.dialog-close')?.focus({preventScroll:true}); return true; }
    catch(error){ console.warn('Встроенный просмотр недоступен — используется прямая ссылка на файл',error); return false; }
  }
  player?.addEventListener('error',()=>{
    if(videoLoadError) videoLoadError.hidden=false;
  });
  document.querySelectorAll('[data-open-video]').forEach(link=>link.addEventListener('click',e=>{
    // Never prevent default unless the native modal actually opens.
    // A direct MP4 link remains usable in restricted iPhone in-app browsers.
    if(!videoDialog || !player || !videoHeading || !link.dataset.videoSrc)return;
    if(!openNative(videoDialog))return;
    e.preventDefault();videoTrigger=link;
    const src=link.dataset.videoSrc;
    videoHeading.textContent=link.dataset.title || 'Видео из портфолио';
    if(videoKicker)videoKicker.textContent=link.dataset.kicker || '«САМАРАМЁН» / ВИДЕО';
    if(videoExternal) {videoExternal.href=src;videoExternal.removeAttribute('download');}
    if(videoLoadError)videoLoadError.hidden=true;
    player.poster=link.dataset.poster || '';
    player.setAttribute('src',src);
    player.load();
  }));
  videoDialog?.addEventListener('close',()=>{
    player?.pause();
    if(videoLoadError)videoLoadError.hidden=true;
    player?.removeAttribute('src');
    player?.load();
    videoTrigger?.focus({preventScroll:true});
  });
  function showSlide(){
    if (!slides.length)return;
    slide.src=slides[active];
    slide.alt=`Слайд ${active+1} из ${slides.length}: карусель «Самые редкие вкусы Buldak»`;
    slideCounter.textContent=`${active+1} / ${slides.length}`;
    if(slideExternal)slideExternal.href=slides[active];
  }
  document.querySelectorAll('[data-open-carousel]').forEach(link=>link.addEventListener('click',e=>{
    if(!galleryDialog || !slide || !slideCounter)return;
    const nextSlides=(link.dataset.slides||'').split('|').filter(Boolean);
    if(!nextSlides.length || !openNative(galleryDialog))return;
    e.preventDefault();carouselTrigger=link;
    slides=nextSlides;
    active=0;showSlide();
  }));
  galleryDialog?.querySelectorAll('[data-move]').forEach(button=>button.addEventListener('click',()=>{
    if (!slides.length)return;
    active=(active+Number(button.dataset.move)+slides.length)%slides.length;showSlide();
  }));
  galleryDialog?.addEventListener('keydown',e=>{
    if (e.key==='ArrowLeft'||e.key==='ArrowRight'){
      e.preventDefault();active=(active+(e.key==='ArrowRight'?1:-1)+slides.length)%slides.length;showSlide();
    }
  });
  galleryDialog?.addEventListener('close',()=>carouselTrigger?.focus({preventScroll:true}));
  document.querySelectorAll('.media-dialog .dialog-close').forEach(button=>button.addEventListener('click',()=>button.closest('dialog')?.close()));
  // Click the dimmed area to close; keep clicks within dialog untouched.
  document.querySelectorAll('dialog.media-dialog').forEach(dialog=>dialog.addEventListener('click',e=>{
    if(e.target===dialog){const r=dialog.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)dialog.close();}
  }));
})();
