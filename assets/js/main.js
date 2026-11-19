const seal = document.querySelector('[data-seal]');

if (seal) {
  // 첫 누름: 봉인이 갈라지고 서임장이 펼쳐진다. 두 번째 누름(또는 6초 뒤): 입장
  const go = () => { location.href = seal.href; };
  const act = (e) => {
    if (e.type === 'keydown' && (e.target === seal || e.metaKey || e.ctrlKey || e.altKey || e.key === 'Tab' || e.key === 'Shift')) return;
    e.preventDefault();
    if (document.body.classList.contains('open')) return go();
    document.body.classList.add('open');
    setTimeout(go, 6000);
  };
  document.addEventListener('click', act);
  document.addEventListener('keydown', act);
} else {
  // 숫자 키 1~4로 메뉴 이동
  document.addEventListener('keydown', (e) => {
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    const a = document.querySelectorAll('.tabs a')[e.key - 1];
    if (a) location.href = a.href;
  });
}
