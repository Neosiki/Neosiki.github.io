const archiveGrid = document.querySelector('#archive-grid');
const archiveFilters = document.querySelectorAll('.archive-filter');
const archiveCount = document.querySelector('#archive-count');

function renderProjectArchive(category = 'all') {
  const visibleProjects = portfolioProjects.filter(project => category === 'all' || project.category === category);
  if (archiveCount) archiveCount.textContent = visibleProjects.length;
  if (!archiveGrid) return;
  if (!visibleProjects.length) {
    archiveGrid.innerHTML = '<p class="archive-empty">이 분야의 프로젝트를 정리하고 있습니다.</p>';
    return;
  }
  archiveGrid.innerHTML = visibleProjects.map(project => {
    const originalIndex = portfolioProjects.indexOf(project) + 1;
    const tag = project.url ? 'a' : 'article';
    const isInternal = project.url && (project.url.startsWith('#') || project.url.endsWith('.html'));
    const linkAttributes = project.url ? ` href="${project.url}"${isInternal ? '' : ' target="_blank" rel="noreferrer"'}` : '';
    const featured = project.featured ? ' · FEATURED' : '';
    const visibility = project.url ? (isInternal ? 'READ CASE' : 'VIEW PROJECT') : 'CASE STUDY';
    const openMark = project.url ? `<span class="archive-open" aria-hidden="true">${isInternal ? '↖' : '↗'}</span>` : '<span class="archive-open" aria-hidden="true">—</span>';
    return `<${tag} class="archive-card ${project.caseStudy || !project.url ? 'case-study' : ''}"${linkAttributes}>
      <img class="archive-image" src="${project.image}" alt="${project.title} 프로젝트를 상징하는 이미지" loading="lazy" />
      <span class="archive-top">
        <span class="archive-number">${String(originalIndex).padStart(2, '0')} / ${project.categoryLabel}</span>
        <span class="archive-visibility">${visibility}${featured}</span>
      </span>
      <span class="archive-category">${project.categoryLabel}</span>
      <h3>${project.title}</h3>
      <p>${project.description}</p>
      <span class="archive-bottom"><span class="archive-language">${project.language}</span>${openMark}</span>
    </${tag}>`;
  }).join('');
}

if (archiveFilters && archiveFilters.length) {
  archiveFilters.forEach(button => {
    button.addEventListener('click', () => {
      archiveFilters.forEach(item => item.classList.remove('active'));
      button.classList.add('active');
      renderProjectArchive(button.dataset.archiveFilter);
    });
  });
}

if (typeof portfolioProjects !== 'undefined') renderProjectArchive();

const projectDialog = document.querySelector('#project-dialog');
const projectDialogImage = document.querySelector('#project-dialog-image');
const projectDialogKicker = document.querySelector('#project-dialog-kicker');
const projectDialogTitle = document.querySelector('#project-dialog-title');
const projectDialogSummary = document.querySelector('#project-dialog-summary');
const projectDialogAudience = document.querySelector('#project-dialog-audience');
const projectDialogScope = document.querySelector('#project-dialog-scope');
const projectDialogOutputs = document.querySelector('#project-dialog-outputs');
const projectDialogApplication = document.querySelector('#project-dialog-application');
const projectDialogLink = document.querySelector('#project-dialog-link');
const projectDetailPresets = {
  public: ['공공기관·연구기관·전략기획팀','공고·정책·시장 자료 조사, 논리 구조화, 검토 절차 설계','제안서·연구기획안·사업계획서·보고서·검토 체크리스트','공공과제 준비, 연구개발 기획, 기관 보고 체계 정비'],
  vibe: ['교육기관·콘텐츠팀·업무 자동화를 검토하는 조직','요구사항 정리, 화면·데이터 흐름 설계, 작동형 웹앱 실습','실습 코드·작동 화면·사용 절차·재현 가능한 교육 자료','신규 서비스 검증, 사내 교육, 반복 업무의 빠른 프로토타이핑'],
  automation: ['중소기업·스타트업·소상공인·제작 운영팀','자료 수집, 문서 처리, 작업 상태 관리, 검수·재처리 흐름 설계','업무 흐름·자동화 규칙·검수 기준·문서 및 운영 가이드','AI·AX 도입, 문서 생산성 개선, 제작 운영의 표준화'],
  journalism: ['언론사·공공 커뮤니케이션팀·데이터 콘텐츠 조직','데이터 수집·검증, 시각화, 기사 구조화, 출처와 근거 관리','데이터셋·시각화·기사 초안·팩트체크표·교육 실습 자료','데이터저널리즘, 뉴스룸 교육, 공공정보 콘텐츠 제작'],
  geo: ['콘텐츠·마케팅·브랜드·검색 유입을 관리하는 조직','검색 질문 분석, 콘텐츠 구조 진단, AI 검색 인용 관점의 개선안 도출','진단 결과·개선 우선순위·콘텐츠 재구성안·운영 체크리스트','SEO·GEO 전략 수립, 콘텐츠 품질 관리, 검색 유입 개선'],
  education: ['교육기관·지원기관·중소기업·스타트업·소상공인','교육 목표 정의, 실습 단계 설계, 현장 적용 과제와 결과물 구성','강의안·실습 자료·사례 문서·평가 기준·후속 적용 가이드','AI교육·컨설팅, 조직 역량 강화, 기관 맞춤형 프로그램 운영'],
  domain: ['기관·미디어·전문 분야 콘텐츠를 기획하는 조직','전문 주제 조사, 메시지 구조화, 편집·브리핑·아카이브 설계','콘텐츠 구조·원고·브리핑 자료·아카이브 기준·편집 레퍼런스','전문 콘텐츠 제작, 리더십 브리핑, 지식 자산화']
};
function openProjectDetail(index){
  const project=portfolioProjects[index]; if(!project||!projectDialog)return;
  const d=projectDetailPresets[project.category]||projectDetailPresets.domain;
  projectDialogImage.src=project.image; projectDialogImage.alt=project.title+' 프로젝트 이미지';
  projectDialogKicker.textContent=String(index+1).padStart(2,'0')+' / '+project.categoryLabel+' · '+project.language;
  projectDialogTitle.textContent=project.title; projectDialogSummary.textContent=project.description;
  projectDialogAudience.textContent=d[0]; projectDialogScope.textContent=d[1]; projectDialogOutputs.textContent=d[2]; projectDialogApplication.textContent=d[3];
  projectDialogLink.href=project.url||'#'; projectDialogLink.hidden=!project.url; projectDialog.showModal();
}
if (archiveGrid) {
  archiveGrid.addEventListener('click',event=>{const card=event.target.closest('.archive-card');if(!card)return;event.preventDefault();const title=card.querySelector('h3')?.textContent;const i=portfolioProjects.findIndex(p=>p.title===title);openProjectDetail(i>=0?i:0);});
}
projectDialog?.addEventListener('click',event=>{if(event.target===projectDialog)projectDialog.close();});
projectDialog?.addEventListener('close',()=>{if(projectDialogImage){projectDialogImage.removeAttribute('src');projectDialogImage.alt='';}});
