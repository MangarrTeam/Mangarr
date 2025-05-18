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