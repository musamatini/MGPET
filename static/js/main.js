// static/js/main.js

document.addEventListener('DOMContentLoaded', function () {
    AOS.init({
        duration: 400,
        once: true,
        offset: 200,
    });

    const navbarElement = document.querySelector('.navbar');
    const heroSectionElement = document.querySelector('.hero-section');
    const bodyElement = document.body;

    let animationDelay = 300;
    let animationDuration = 500;

    if (navbarElement) {
        const computedStyle = getComputedStyle(navbarElement);
        const delayProp = computedStyle.getPropertyValue('--navbar-animation-delay').trim();
        const durationProp = computedStyle.getPropertyValue('--navbar-animation-duration').trim();

        if (delayProp.endsWith('s')) animationDelay = parseFloat(delayProp) * 1000;
        else if (delayProp.endsWith('ms')) animationDelay = parseFloat(delayProp);

        if (durationProp.endsWith('s')) animationDuration = parseFloat(durationProp) * 1000;
        else if (durationProp.endsWith('ms')) animationDuration = parseFloat(durationProp);
    }
    const totalAnimationTime = animationDelay + animationDuration;


    if (navbarElement && bodyElement) {
        const currentPathOnly = window.location.pathname; 
        const hasHash = window.location.hash && window.location.hash.length > 1; 

        const homePageBasePaths = ['/', '/en/', '/ar/']; 

        let isCleanHomepage = false;
        for (const basePath of homePageBasePaths) {
            if (currentPathOnly === basePath || currentPathOnly === basePath.slice(0, -1)) {
                isCleanHomepage = true;
                break;
            }
        }
        
        // Condition for main animation: hero exists, it's a clean homepage (correct path AND no hash)
        if (heroSectionElement && isCleanHomepage && !hasHash) {
            console.log("Clean Homepage (no hash): Preparing push animation.");

            bodyElement.classList.remove('initial-animation--done');
            bodyElement.classList.remove('initial-animation--active');
            
            bodyElement.classList.add('initial-animation--active');
            navbarElement.classList.add('animation-initial-state'); // Assumes CSS for this sets initial anim props
            heroSectionElement.classList.add('animation-initial-state'); // Same for hero

            void navbarElement.offsetHeight; // Force reflow

            console.log("Running push animation.");
            navbarElement.classList.remove('animation-initial-state'); // Removing this triggers transition to final state
            heroSectionElement.classList.remove('animation-initial-state');

            setTimeout(() => {
                console.log("Push animation finished. Cleaning up.");
                if (bodyElement.classList.contains('initial-animation--active')) {
                    bodyElement.classList.remove('initial-animation--active');
                }
                bodyElement.classList.add('initial-animation--done');
            }, totalAnimationTime);

        } else {
            // Not a "clean" homepage, or it has a hash (e.g. /#about), or no hero section: 
            // Apply final layout directly and *instantly* without the main push animation.
            if (hasHash && isCleanHomepage) {
                console.log("Homepage with hash (" + window.location.hash + "): Applying standard layout instantly, no navbar animation.");
            } else if (!heroSectionElement && isCleanHomepage) {
                console.log("Homepage but no hero section found. Applying standard layout instantly, no navbar animation.");
            } else if (!isCleanHomepage) {
                console.log("Not a base homepage path (" + currentPathOnly + "): Applying standard layout instantly, no navbar animation.");
            }
            
            bodyElement.classList.remove('initial-animation--active'); 
            bodyElement.classList.add('initial-animation--done');     
            
            if (navbarElement) {
                // MODIFICATION START: Apply styles instantly
                // Add the .no-transition class to temporarily disable CSS transitions
                navbarElement.classList.add('no-transition');

                // Apply final, visible styles
                navbarElement.style.opacity = '1';
                navbarElement.style.transform = 'translateY(0)';
                
                // Ensure any class that defines an initial (e.g., hidden) state for animation is removed
                navbarElement.classList.remove('animation-initial-state');

                // Force reflow/repaint. This ensures the styles are applied *now*, without transition.
                // Reading a property like offsetHeight is a common way to trigger this.
                void navbarElement.offsetHeight; 

                // Remove the .no-transition class so transitions work for subsequent interactions (e.g., scroll, hover)
                navbarElement.classList.remove('no-transition');
                // MODIFICATION END
            }
        }
    } else {
        if (!navbarElement) console.error("Navbar element NOT found.");
        // If body exists but navbar doesn't, still mark animation as "done" for consistency
        if (bodyElement) {
             bodyElement.classList.remove('initial-animation--active');
             bodyElement.classList.add('initial-animation--done');
        }
    }

    // --- HERO SWIPER ---
    // ... (rest of your Swiper code remains unchanged)
    const heroSwiper = new Swiper('.hero-swiper', {
        effect: 'slide',
        loop: true,
        autoplay: {
            delay: 6000,
            disableOnInteraction: false,
        },
        speed: 900,
        grabCursor: true,
        pagination: {
            el: '.swiper-pagination',
            clickable: true,
            dynamicBullets: true,
        },
        navigation: {
            nextEl: '.swiper-button-next',
            prevEl: '.swiper-button-prev',
        },
        on: {
            init: function () {
                const activeSlideOnInit = this.slides[this.activeIndex];
                if (activeSlideOnInit) {
                    const caption = activeSlideOnInit.querySelector('.slide-caption');
                    if (caption) caption.classList.add('is-visible');
                }
            },
            slideChangeTransitionStart: function () {
                const nextActiveSlide = this.slides[this.activeIndex];
                if (nextActiveSlide) {
                    const caption = nextActiveSlide.querySelector('.slide-caption');
                    if (caption) caption.classList.add('is-visible');
                }
                this.slides.forEach((slide, index) => {
                    if (index !== this.activeIndex) {
                        const caption = slide.querySelector('.slide-caption');
                        if (caption) caption.classList.remove('is-visible');
                    }
                });
            }
        }
    });

    // --- MOBILE MENU TOGGLE ---
    // ... (your mobile menu code remains unchanged)
    const menuToggle = document.querySelector('.mobile-menu-toggle');
    const mobileNav = document.querySelector('.navbar-links-mobile');
    if (menuToggle && mobileNav) {
        menuToggle.addEventListener('click', () => {
            mobileNav.classList.toggle('active');
            const isExpanded = mobileNav.classList.contains('active');
            menuToggle.setAttribute('aria-expanded', isExpanded);
            menuToggle.querySelector('i').classList.toggle('fa-bars');
            menuToggle.querySelector('i').classList.toggle('fa-times');
        });
    }

    // --- SMOOTH SCROLL WITH NAVBAR OFFSET ---
    // ... (your smooth scroll code remains unchanged)
    document.querySelectorAll('a[href^="#"], a[href*="/#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            let targetId = href.substring(href.lastIndexOf('#')); 
            
            const isPureHash = href.startsWith('#');
            const isPathWithHash = href.includes('/#');

            const currentPathname = window.location.pathname;
            const linkPathname = href.split('#')[0];

            let shouldSmoothScroll = false;
            if (isPureHash) {
                shouldSmoothScroll = true;
            } else if (isPathWithHash) {
                // Check if the linkPathname (part before #) matches current OR is a homepage base path
                if (linkPathname === currentPathname || linkPathname === "" || homePageBasePaths.some(p => linkPathname === p || linkPathname === p.slice(0, -1))) {
                    shouldSmoothScroll = true;
                }
            }

            if (shouldSmoothScroll && targetId.length > 1 && document.querySelector(targetId)) {
                e.preventDefault();
                const targetElement = document.querySelector(targetId);
                const navbarHeight = document.querySelector('.navbar')?.offsetHeight || 70; // Use navbarElement if preferred and in scope
                
                const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
                const targetPositionInDocument = targetElement.getBoundingClientRect().top + scrollTop;
                const offsetPosition = targetPositionInDocument - navbarHeight;

                window.scrollTo({
                    top: offsetPosition,
                    behavior: 'smooth'
                });

                if (mobileNav && mobileNav.classList.contains('active')) {
                    mobileNav.classList.remove('active');
                    menuToggle.setAttribute('aria-expanded', 'false');
                    menuToggle.querySelector('i').classList.add('fa-bars');
                    menuToggle.querySelector('i').classList.remove('fa-times');
                }
            }
            // If not shouldSmoothScroll, let the browser handle it (it might be a link to a different page with a hash)
        });
    });

    // --- STICKY NAVBAR SCROLL EFFECT ---
    const navbarScrollEffect = document.querySelector('.navbar'); // This is the same as navbarElement
    if (navbarScrollEffect) { 
        window.addEventListener('scroll', () => {
            if (window.scrollY > 50) {
                navbarScrollEffect.classList.add('scrolled');
            } else {
                navbarScrollEffect.classList.remove('scrolled');
            }
        });
    }

     // --- ACTIVE NAV LINKS --- 
    const navLinks = document.querySelectorAll('.navbar-links-desktop ul li a, .navbar-links-mobile ul li a');
    const currentPath = window.location.pathname; // This is essentially currentPathOnly
    navLinks.forEach(link => {
        link.classList.remove('active');
        const linkHref = link.getAttribute('href');
        // Simplified active link logic slightly for clarity, original was likely fine
        if (linkHref === currentPath || (linkHref.length > 1 && linkHref !== '/' && currentPath.startsWith(linkHref)) ) {
            link.classList.add('active');
        } else if (currentPath === '/' && (linkHref === '/' || linkHref.endsWith('#home') || linkHref.endsWith('/#home'))) {
             link.classList.add('active');
        }
    });

    // --- CTA SECTION EXPAND ANIMATION --- 
    const ctaSection = document.querySelector('.cta-expand-reveal');
    if (ctaSection) {
        const ctaObserver = new IntersectionObserver((entries, observer) => { 
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('is-visible');
                    observer.unobserve(entry.target); 
                }
            });
        }, { threshold: 0.3 }); 
        ctaObserver.observe(ctaSection);
    }
});