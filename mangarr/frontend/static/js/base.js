  function updateSidebarHeight() {
    const navbar = document.querySelector('nav.navbar');
    const sidebar = document.getElementById('sidebar');
    if (!navbar || !sidebar) return;
    
    const navHeight = navbar.offsetHeight;
    sidebar.style.top = navHeight + 'px';
    sidebar.style.bottom = 0;
    //sidebar.style.height = `calc(100vh - ${navHeight}px)`;
  }

  function updateMainHeight() {
    const navbar = document.querySelector('nav.navbar');
    const main = document.getElementById('content');
    if (!navbar || !main) return;
    
    const navHeight = navbar.offsetHeight;
    main.style.paddingTop = navHeight + 'px';
    const resultsBox = document.getElementById('searchResults');
    if (!resultsBox) return;
    resultsBox.style.top = `calc(${navHeight}px - 0.5rem)`;
  }

  window.addEventListener('load', updateSidebarHeight);
  window.addEventListener('resize', updateSidebarHeight);
  window.addEventListener('load', updateMainHeight);
  window.addEventListener('resize', updateMainHeight);

  const sidebar = document.getElementById('sidebar');
  const toggleBtn = document.getElementById('sidebarToggle');

  toggleBtn.addEventListener('click', () => {
    sidebar.classList.toggle('show');
  });


function fetchInit(loadingId, buttonId) {
  const loadingEl = document.getElementById(loadingId);
  const buttonEl = document.getElementById(buttonId);
  if (loadingEl) {
    loadingEl.classList.remove('hidden');
  }
  if (buttonEl) {
    buttonEl.disabled = true;
  }
}

function fetchSuccess(loadingId, successId, buttonId) {
  const loadingEl = document.getElementById(loadingId);
  const successEl = document.getElementById(successId);
  const buttonEl = document.getElementById(buttonId);

  if (loadingEl) loadingEl.classList.add('hidden');
  if (successEl) {
    successEl.classList.remove('hidden');
    successEl.style.opacity = 1;
    setTimeout(() => {
      successEl.classList.add('fade-out');
      setTimeout(() => {
        successEl.classList.add('hidden');
        successEl.classList.remove('fade-out');
        successEl.style.opacity = 1;
      }, 500);
    }, 2000);
  }
  if (buttonEl) {
    buttonEl.disabled = false;
  }
}

function fetchFail(loadingId, failId, buttonId) {
  const loadingEl = document.getElementById(loadingId);
  const failEl = document.getElementById(failId);
  const buttonEl = document.getElementById(buttonId);

  if (loadingEl) loadingEl.classList.add('hidden');
  if (failEl) {
    failEl.classList.remove('hidden');
    failEl.style.opacity = 1;
    setTimeout(() => {
      failEl.classList.add('fade-out');
      setTimeout(() => {
        failEl.classList.add('hidden');
        failEl.classList.remove('fade-out');
        failEl.style.opacity = 1;
      }, 500);
    }, 2000);
  }
  if (buttonEl) {
    buttonEl.disabled = false;
  }
}