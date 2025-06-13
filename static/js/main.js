// static/js/main.js

document.addEventListener('DOMContentLoaded', function () {
    // ... (AOS init, variable declarations) ...
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
        const currentFullUrl = window.location.href; // Get the full URL
        const currentPathOnly = window.location.pathname; // Path without hash or query
        const hasHash = window.location.hash && window.location.hash.length > 1; // Check if there's a non-empty hash

        const homePageBasePaths = ['/', '/en/', '/ar/']; // Base paths for homepage (note trailing slashes)

        // Determine if it's a "clean" homepage load (correct base path AND no hash)
        // We use startsWith to handle cases like /en/ vs /en
        // And ensure the path is one of the exact homePageBasePaths or its non-trailing-slash version
        let isCleanHomepage = false;
        for (const basePath of homePageBasePaths) {
            if (currentPathOnly === basePath || currentPathOnly === basePath.slice(0, -1) /* remove trailing slash for comparison */) {
                isCleanHomepage = true;
                break;
            }
        }
        
        // Condition for animation: hero exists, it's a clean homepage (correct path AND no hash)
        if (heroSectionElement && isCleanHomepage && !hasHash) {
            console.log("Clean Homepage (no hash): Preparing push animation.");

            bodyElement.classList.remove('initial-animation--done');
            bodyElement.classList.remove('initial-animation--active');
            
            bodyElement.classList.add('initial-animation--active');
            navbarElement.classList.add('animation-initial-state');
            heroSectionElement.classList.add('animation-initial-state');

            void navbarElement.offsetHeight;

            console.log("Running push animation.");
            navbarElement.classList.remove('animation-initial-state');
            heroSectionElement.classList.remove('animation-initial-state');

            setTimeout(() => {
                console.log("Push animation finished. Cleaning up.");
                if (bodyElement.classList.contains('initial-animation--active')) {
                    bodyElement.classList.remove('initial-animation--active');
                }
                bodyElement.classList.add('initial-animation--done');
            }, totalAnimationTime);

        } else {
            // Not a "clean" homepage, or no hero section: Apply final layout directly.
            if (hasHash && isCleanHomepage) {
                console.log("Homepage with hash (e.g., /#about): Applying standard layout directly.");
            } else if (!heroSectionElement && isCleanHomepage) {
                console.log("Homepage but no hero section found. Applying standard layout directly.");
            } else if (!isCleanHomepage) {
                console.log("Not a base homepage path: Applying standard layout directly.");
            }
            
            bodyElement.classList.remove('initial-animation--active');
            bodyElement.classList.add('initial-animation--done');
            
            if (navbarElement) {
                navbarElement.style.opacity = '1';
                navbarElement.style.transform = 'translateY(0)';
                navbarElement.classList.remove('animation-initial-state');
            }
        }
    } else {
        if (!navbarElement) console.error("Navbar element NOT found.");
        if (bodyElement) {
             bodyElement.classList.remove('initial-animation--active');
             bodyElement.classList.add('initial-animation--done');
        }
    }

    // --- HERO SWIPER ---
    // ... (rest of your Swiper code)
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
    // ... (your mobile menu code)
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
    // Make sure your smooth scroll handles internal page links correctly
    document.querySelectorAll('a[href^="#"], a[href*="/#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            let targetId = href.substring(href.lastIndexOf('#')); // Keep this for finding element
            
            // Check if the link is purely a hash for the current page, or a full path with a hash
            const isPureHash = href.startsWith('#');
            const isPathWithHash = href.includes('/#');

            // Only proceed with smooth scroll if it's a link on the *current page* or a root-relative link to a hash on the homepage
            const currentPathname = window.location.pathname;
            const linkPathname = href.split('#')[0];

            // Condition for smooth scroll:
            // 1. Pure hash on any page.
            // 2. Path with hash IF the path part matches current page's path OR if it's a root path link (e.g. "/#about" from "/products")
            let shouldSmoothScroll = false;
            if (isPureHash) {
                shouldSmoothScroll = true;
            } else if (isPathWithHash) {
                if (linkPathname === currentPathname || linkPathname === "" || homePageBasePaths.some(p => linkPathname === p || linkPathname === p.slice(0, -1))) {
                     // Check if the linkPathname (part before #) matches current OR is a homepage base path
                    shouldSmoothScroll = true;
                }
            }


            if (shouldSmoothScroll && targetId.length > 1 && document.querySelector(targetId)) {
                e.preventDefault();
                const targetElement = document.querySelector(targetId);
                const navbarHeight = document.querySelector('.navbar')?.offsetHeight || 70;
                
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
    // ... (your sticky navbar code)
    const navbarScrollEffect = document.querySelector('.navbar');
    if (navbarScrollEffect) {
        window.addEventListener('scroll', () => {
            if (window.scrollY > 50) {
                navbarScrollEffect.classList.add('scrolled');
            } else {
                navbarScrollEffect.classList.remove('scrolled');
            }
        });
    }

     // --- ACTIVE NAV LINKS --- (Keep this)
    const navLinks = document.querySelectorAll('.navbar-links-desktop ul li a, .navbar-links-mobile ul li a');
    const currentPath = window.location.pathname;
    navLinks.forEach(link => {
        link.classList.remove('active');
        const linkHref = link.getAttribute('href');
        if (linkHref === currentPath || (linkHref !== '/' && currentPath.startsWith(linkHref) && linkHref.length > 1) ) {
            link.classList.add('active');
        } else if (currentPath === '/' && (linkHref === '/' || linkHref.endsWith('#home'))) {
             link.classList.add('active');
        }
    });

    // --- CTA SECTION EXPAND ANIMATION --- (Keep this)
    const ctaSection = document.querySelector('.cta-expand-reveal');
    if (ctaSection) {
        const ctaObserver = new IntersectionObserver((entries, observer) => { // Add 'observer' to the callback arguments
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('is-visible');
                    observer.unobserve(entry.target); // <<< STOP OBSERVING AFTER THE FIRST TIME
                }
                // REMOVE the 'else' block: entry.target.classList.remove('is-visible');
            });
        }, { threshold: 0.3 }); 
        ctaObserver.observe(ctaSection);
    }
});