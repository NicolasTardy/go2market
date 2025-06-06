/* ==========================================================================
   Script générique du mini-site DartyMax Promo HG
   - Smooth scroll sur les ancres
   - Mini burger pour mobiles (facultatif si vous ajoutez un menu)
   - Suppression automatique des focus outline sur clic souris
========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
  /* Smooth scroll pour tous les liens internes commençant par # */
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e){
      e.preventDefault();
      const target = document.querySelector(this.getAttribute('href'));
      if(target){
        target.scrollIntoView({ behavior:'smooth', block:'start' });
      }
    });
  });

  /* Exemple de menu burger (décommentez si vous ajoutez un burger)
  const burger = document.getElementById('burger');
  const nav = document.querySelector('.main-nav');
  if(burger){
    burger.addEventListener('click', ()=>{
      nav.classList.toggle('open');
      burger.classList.toggle('active');
    });
  }
  */

  /* Supprime les outlines (accessibilité ok car toujours présent via clavier) */
  function handleFirstTab(e){
    if(e.key === 'Tab'){
      document.body.classList.add('user-is-tabbing');
      window.removeEventListener('keydown', handleFirstTab);
    }
  }
  window.addEventListener('keydown', handleFirstTab);
});