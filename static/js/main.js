// static/js/main.js

let mainContentLoaded = false; // Global flag to prevent multiple initializations

// This function will initialize Swiper, AOS, and other content that depends on the page being ready
function initializeMainContent() {
    if (mainContentLoaded) {
        // console.log("Main content already initialized.");
        return;
    }
    mainContentLoaded = true;
    // console.log("InitializeMainContent: Starting...");

    // Ensure preloader is fully removed from layout now
    const preloaderElement = document.getElementById('preloader');
    if (preloaderElement) {
        preloaderElement.style.display = 'none';
        // console.log("InitializeMainContent: Preloader display set to none.");
    }

    // --- HERO SWIPER ---
    if (document.querySelector('.hero-swiper')) {
        const heroSwiper = new Swiper('.hero-swiper', {
            effect: 'slide',
            loop: true,
            autoplay: {
                delay: 6000,
                disableOnInteraction: false,
            },
            speed: 600,
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
            keyboard: {
                enabled: true,
                onlyInViewport: true,
            },
            mousewheel: {
                enabled: true,
                forceToAxis: true,
            },
            on: {
                init: function () {
                    // console.log("Swiper init event fired.");
                    const activeSlideOnInit = this.slides[this.activeIndex];
                    if (activeSlideOnInit) {
                        const caption = activeSlideOnInit.querySelector('.slide-caption');
                        if (caption) {
                            // This small timeout allows the browser a frame to render the slide
                            // before the caption animation starts, making it smoother.
                            // Try 0ms or 50ms.
                            setTimeout(() => {
                                caption.classList.add('is-visible');
                                // console.log("Initial Swiper caption made visible.");
                            }, 50);
                        }
                    }
                },
                slideChangeTransitionStart: function () {
                    this.slides.forEach((slide) => {
                        const caption = slide.querySelector('.slide-caption');
                        if (caption) caption.classList.remove('is-visible');
                    });
                },
                slideChangeTransitionEnd: function () {
                    const currentActiveSlide = this.slides[this.activeIndex];
                    if (currentActiveSlide) {
                        const caption = currentActiveSlide.querySelector('.slide-caption');
                        if (caption) {
                            caption.classList.add('is-visible');
                        }
                    }
                }
            }
        });
        // console.log("Hero Swiper Initialized.");
    } else {
        // console.log("Hero Swiper not found on this page.");
    }

    // --- AOS INITIALIZATION ---
    AOS.init({
        duration: 400,
        once: true,
        offset: 200,
    });
    // console.log("AOS Initialized.");

    // --- CTA SECTION EXPAND ANIMATION ---
    const ctaSection = document.querySelector('.cta-expand-reveal');
    if (ctaSection) {
        const ctaObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('is-visible');
                    observer.unobserve(entry.target);
                    // console.log("CTA section is visible and animated.");
                }
            });
        }, { threshold: 0.3 });
        ctaObserver.observe(ctaSection);
    }
    // console.log("InitializeMainContent: Finished.");
}


document.addEventListener('DOMContentLoaded', function () {
    // console.log("DOMContentLoaded event fired.");

    const preloader = document.getElementById('preloader');
    const navbarElement = document.querySelector('.navbar');
    const heroSectionElement = document.querySelector('.hero-section');
    const bodyElement = document.body;

    if ('history' in window && 'scrollRestoration' in history) {
        history.scrollRestoration = 'manual';
    }

    let navbarAnimationDelay = 300;
    let navbarAnimationDuration = 500;
    if (navbarElement) {
        const computedStyle = getComputedStyle(navbarElement);
        const delayProp = computedStyle.getPropertyValue('--navbar-animation-delay').trim();
        const durationProp = computedStyle.getPropertyValue('--navbar-animation-duration').trim();
        if (delayProp.endsWith('s')) navbarAnimationDelay = parseFloat(delayProp) * 1000;
        else if (delayProp.endsWith('ms')) navbarAnimationDelay = parseFloat(delayProp);
        if (durationProp.endsWith('s')) navbarAnimationDuration = parseFloat(durationProp) * 1000;
        else if (durationProp.endsWith('ms')) navbarAnimationDuration = parseFloat(durationProp);
    }
    const totalNavbarAnimationTime = navbarAnimationDelay + navbarAnimationDuration;
    // Preloader CSS: opacity 0.5s ease-out 0.2s, visibility 0s linear 0.7s
    // Total visual fade-out time for preloader is 0.2s (delay) + 0.5s (opacity) = 700ms
    const preloaderFadeOutDuration = 700;

    const currentPathOnly = window.location.pathname;
    const hasHash = window.location.hash && window.location.hash.length > 1;
    const homePageBasePaths = ['/', '/en/', '/ar/'];
    let isCleanHomepage = homePageBasePaths.some(basePath => currentPathOnly === basePath || currentPathOnly === basePath.slice(0, -1));
    const willRunPushBothAnimation = heroSectionElement && isCleanHomepage && !hasHash;

    // --- START PRELOADER FADE-OUT IMMEDIATELY ---
    if (preloader) {
        preloader.classList.add('loaded');
        // console.log(`Preloader 'loaded' class added. Visual fade-out will take ${preloaderFadeOutDuration}ms.`);
    } else {
        // console.log("Preloader element not found.");
    }

    let timeUntilPushBothEnds = 0; // Time until the push-both animation finishes, if it runs

    if (willRunPushBothAnimation && navbarElement && heroSectionElement && bodyElement) {
        // console.log("Clean Homepage: Preparing PUSH-BOTH animation.");
        bodyElement.classList.remove('initial-animation--done', 'initial-animation--active');
        navbarElement.classList.remove('animation-initial-state');
        heroSectionElement.classList.remove('animation-initial-state');

        bodyElement.classList.add('initial-animation--active');
        navbarElement.classList.add('animation-initial-state');
        heroSectionElement.classList.add('animation-initial-state');

        void navbarElement.offsetHeight;
        void heroSectionElement.offsetHeight;

        // console.log(`Running PUSH-BOTH animation. It will take ${totalNavbarAnimationTime}ms.`);
        navbarElement.classList.remove('animation-initial-state');
        heroSectionElement.classList.remove('animation-initial-state');

        timeUntilPushBothEnds = totalNavbarAnimationTime;

        setTimeout(() => {
            // console.log("PUSH-BOTH animation finished.");
            if (bodyElement.classList.contains('initial-animation--active')) {
                bodyElement.classList.remove('initial-animation--active');
            }
            bodyElement.classList.add('initial-animation--done');
        }, totalNavbarAnimationTime);

    } else {
        // console.log("Not a clean homepage or missing elements: Applying standard layout instantly.");
        if (bodyElement) {
            bodyElement.classList.remove('initial-animation--active');
            bodyElement.classList.add('initial-animation--done');
        }
        if (navbarElement) {
            navbarElement.classList.add('no-transition');
            navbarElement.style.opacity = '1';
            navbarElement.style.transform = 'translateY(0)';
            navbarElement.classList.remove('animation-initial-state');
            void navbarElement.offsetHeight;
            navbarElement.classList.remove('no-transition');
        }
        if (heroSectionElement) {
            heroSectionElement.classList.add('no-transition');
            heroSectionElement.classList.remove('animation-initial-state');
            void heroSectionElement.offsetHeight;
            heroSectionElement.classList.remove('no-transition');
        }
    }

    // Determine the actual delay needed before initializing main content.
    // It's the longer of the preloader fade time or the push-both animation time.
    const delayForContentInitialization = Math.max(
        timeUntilPushBothEnds,
        preloader ? preloaderFadeOutDuration : 0
    );

    // console.log(`Main content (Swiper, etc.) will be initialized after ${delayForContentInitialization}ms.`);
    setTimeout(initializeMainContent, delayForContentInitialization);


    // --- Other UI elements that can be initialized independently ---
    // (Mobile Menu, Smooth Scroll, Sticky Navbar, Active Nav Links - as in your original code)
    // --- MOBILE MENU TOGGLE ---
    const menuToggle = document.querySelector('.mobile-menu-toggle');
    const mobileNav = document.querySelector('.navbar-links-mobile');
    if (menuToggle && mobileNav) { /* ... your existing logic ... */ }
    // --- SMOOTH SCROLL WITH NAVBAR OFFSET ---
    document.querySelectorAll('a[href^="#"], a[href*="/#"]').forEach(anchor => { /* ... */ });
    // --- STICKY NAVBAR SCROLL EFFECT ---
    if (navbarElement) { /* ... */ }
    // --- ACTIVE NAV LINKS ---
    const navLinks = document.querySelectorAll('.navbar-links-desktop ul li a, .navbar-links-mobile ul li a');
    navLinks.forEach(link => { /* ... */ });

}); // End of DOMContentLoaded

window.addEventListener('load', () => {
    if (!mainContentLoaded) {
        // console.warn("Window.load fallback: Main content not initialized by DOMContentLoaded. Forcing init.");
        const preloader = document.getElementById('preloader');
        const preloaderFadeOutDuration = 700; // Define it here again for standalone use

        if (preloader && !preloader.classList.contains('loaded')) {
            preloader.classList.add('loaded');
            // If preloader wasn't even started, wait for its fade + a buffer
            setTimeout(initializeMainContent, preloaderFadeOutDuration + 50);
        } else if (preloader) {
            // Preloader started fading but content not initted, wait for remaining fade + buffer
            setTimeout(initializeMainContent, preloaderFadeOutDuration - parseFloat(getComputedStyle(preloader).opacity)*preloaderFadeOutDuration + 50 ) // Approx remaining time
        }
         else {
            // No preloader, or it's already handled, init with small safety delay
            setTimeout(initializeMainContent, 50);
        }
    } else {
        // console.log("Window.load: Main content already handled.");
    }
});