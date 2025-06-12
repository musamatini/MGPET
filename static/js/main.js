// static/js/main.js
document.addEventListener('DOMContentLoaded', function () {
    // Initialize AOS (Animate on Scroll) - Keep this for other sections
    AOS.init({
        duration: 800,
        once: true,
        offset: 100,  
    });

    // --- HERO SWIPER ---
    const heroSwiper = new Swiper('.hero-swiper', {
        // --- NEW SLIDE EFFECT ---
        effect: 'slide', // Change from 'fade' to 'slide' or 'creative'
        creativeEffect: {
            prev: {
                shadow: true,
                translate: ['-120%', 0, -500],
                rotate: [0, 0, -20],
            },
            next: {
                shadow: true,
                translate: ['120%', 0, -500],
                rotate: [0, 0, 20],
            },
        },
        loop: true,
        autoplay: {
            delay: 7000, // Slightly longer delay for more complex animations
            disableOnInteraction: false,
        },
        speed: 800, // Speed of slide transition
        grabCursor: true, // Show grab cursor on hover
        pagination: {
            el: '.swiper-pagination',
            clickable: true,
        },
        navigation: {
            nextEl: '.swiper-button-next',
            prevEl: '.swiper-button-prev',
        },
        // --- ANIMATE CONTENT ON SLIDE CHANGE ---
        on: {
            init: function () {
                // Animate content of the initial active slide
                animateSwiperSlideContent(this.slides[this.activeIndex]);
            },
            slideChangeTransitionStart: function () {
                // Reset animation for all slides before transition
                this.slides.forEach(slide => {
                    const caption = slide.querySelector('.slide-caption');
                    if (caption) {
                        caption.classList.remove('is-visible');
                        // Optionally reset individual elements if needed
                        // caption.querySelectorAll('.animate-on-slide').forEach(el => el.classList.remove('animated'));
                    }
                });
            },
            slideChangeTransitionEnd: function () {
                // Animate content of the new active slide
                animateSwiperSlideContent(this.slides[this.activeIndex]);
            },
        },
    });

    function animateSwiperSlideContent(activeSlide) {
        const caption = activeSlide.querySelector('.slide-caption');
        if (caption) {
            // Add a class to trigger CSS animations on the caption and its children
            caption.classList.add('is-visible');

            // Example of staggered animation for children (can be done with CSS or JS)
            const elementsToAnimate = caption.querySelectorAll('.animate-this');
            elementsToAnimate.forEach((el, index) => {
                el.style.setProperty('--animation-delay-multiplier', index);
                // The actual animation will be defined in CSS using this class
                // No need to add/remove 'animated' class here if CSS handles it via 'is-visible' parent
            });
        }
    }


    // Mobile Menu Toggle (keep existing code)
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

    // Smooth scroll for internal links (keep existing code)
    document.querySelectorAll('a[href^="#"], a[href*="/#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            const targetId = href.substring(href.lastIndexOf('#'));
            if (targetId.length > 1 && document.querySelector(targetId)) {
                if (window.location.pathname === '/' || href.startsWith('/#') || (href.startsWith('#') && window.location.pathname === '/')) {
                    e.preventDefault();
                    document.querySelector(targetId).scrollIntoView({ behavior: 'smooth' });
                    if (mobileNav && mobileNav.classList.contains('active')) {
                        mobileNav.classList.remove('active');
                        menuToggle.setAttribute('aria-expanded', 'false');
                        menuToggle.querySelector('i').classList.add('fa-bars');
                        menuToggle.querySelector('i').classList.remove('fa-times');
                    }
                }
            }
        });
    });

    // Sticky Navbar background change on scroll (keep existing code)
    const navbar = document.querySelector('.navbar.sticky-top');
    if (navbar) {
        window.addEventListener('scroll', () => {
            if (window.scrollY > 50) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        });
    }

    // Active nav links (keep existing code)
    const navLinks = document.querySelectorAll('.navbar-links-desktop ul li a, .navbar-links-mobile ul li a');
    const currentPath = window.location.pathname;
    const currentHash = window.location.hash;

    navLinks.forEach(link => {
        const linkHref = link.getAttribute('href');
        if (linkHref === currentPath && currentPath !== '/' && !linkHref.includes('#')) {
            link.classList.add('active');
        }
        if (currentPath === '/' || linkHref.startsWith('/#')) {
            const anchor = linkHref.substring(linkHref.lastIndexOf('#'));
            // Simplified active state for homepage initial load
            if ((currentHash === '' && (anchor === '#home' || linkHref === '/')) || anchor === currentHash) {
                 link.classList.add('active');
            }
        }
    });

    const animatedSections = document.querySelectorAll('.cta-horizontal-reveal'); // Add other classes here for similar behavior

    const sectionObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('is-visible');
                observer.unobserve(entry.target); // Optional: stop observing once animated
            }
        });
    }, {
        root: null, // relative to document viewport
        threshold: 0.1, // trigger when 10% of the element is visible
        // rootMargin: '-50px 0px -50px 0px' // Optional: adjust when it triggers
    });

    animatedSections.forEach(section => {
        sectionObserver.observe(section);
    });


    if (currentPath === '/') {
        const sections = document.querySelectorAll('section[id]');
        window.addEventListener('scroll', () => {
            let currentActive = '';
            sections.forEach(section => {
                const sectionTop = section.offsetTop - (navbar ? navbar.offsetHeight : 70) - 50;
                if (window.scrollY >= sectionTop) {
                    currentActive = '#' + section.getAttribute('id');
                }
            });
            
            navLinks.forEach(link => {
                const linkHref = link.getAttribute('href');
                const linkAnchor = linkHref.substring(linkHref.lastIndexOf('#'));
                link.classList.remove('active');
                if (linkAnchor === currentActive || (currentActive === '' && (linkAnchor === '#home' || linkHref === '/')) ) {
                    link.classList.add('active');
                } else if (linkHref === '/' && currentActive === '#home') {
                    link.classList.add('active');
                }
            });
        });
        // Trigger scroll once on load to set initial active state if not at top
        if(window.scrollY > 0) window.dispatchEvent(new Event('scroll'));
    }
});