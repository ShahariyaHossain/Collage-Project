(function ($) {
    "use strict";

    $(document).ready(function ($) {

        // testimonial sliders
        $(".testimonial-sliders").owlCarousel({
            items: 1,
            loop: true,
            autoplay: true,
            responsive: {
                0: {
                    items: 1,
                    nav: false
                },
                600: {
                    items: 1,
                    nav: false
                },
                1000: {
                    items: 1,
                    nav: false,
                    loop: true
                }
            }
        });

        // homepage slider
        $(".homepage-slider").owlCarousel({
            items: 1,
            loop: true,
            autoplay: true,
            nav: true,
            dots: false,
            navText: ['<i class="fas fa-angle-left"></i>', '<i class="fas fa-angle-right"></i>'],
            responsive: {
                0: {
                    items: 1,
                    nav: false,
                    loop: true
                },
                600: {
                    items: 1,
                    nav: true,
                    loop: true
                },
                1000: {
                    items: 1,
                    nav: true,
                    loop: true
                }
            }
        });

        // logo carousel
        $(".logo-carousel-inner").owlCarousel({
            items: 4,
            loop: true,
            autoplay: true,
            margin: 30,
            responsive: {
                0: {
                    items: 1,
                    nav: false
                },
                600: {
                    items: 3,
                    nav: false
                },
                1000: {
                    items: 4,
                    nav: false,
                    loop: true
                }
            }
        });

        // count down
        if ($('.time-countdown').length) {
            $('.time-countdown').each(function () {
                var $this = $(this), finalDate = $(this).data('countdown');
                $this.countdown(finalDate, function (event) {
                    var $this = $(this).html(event.strftime('' + '<div class="counter-column"><div class="inner"><span class="count">%D</span>Days</div></div> ' + '<div class="counter-column"><div class="inner"><span class="count">%H</span>Hours</div></div>  ' + '<div class="counter-column"><div class="inner"><span class="count">%M</span>Mins</div></div>  ' + '<div class="counter-column"><div class="inner"><span class="count">%S</span>Secs</div></div>'));
                });
            });
        }

        // projects filters isotop
        $(".product-filters li").on('click', function () {

            $(".product-filters li").removeClass("active");
            $(this).addClass("active");

            var selector = $(this).attr('data-filter');

            $(".product-lists").isotope({
                filter: selector,
            });

        });

        // isotop inner
        $(".product-lists").isotope();

        // magnific popup
        $('.popup-youtube').magnificPopup({
            disableOn: 700,
            type: 'iframe',
            mainClass: 'mfp-fade',
            removalDelay: 160,
            preloader: false,
            fixedContentPos: false
        });

        // light box
        $('.image-popup-vertical-fit').magnificPopup({
            type: 'image',
            closeOnContentClick: true,
            mainClass: 'mfp-img-mobile',
            image: {
                verticalFit: true
            }
        });

        // homepage slides animations
        $(".homepage-slider").on("translate.owl.carousel", function () {
            $(".hero-text-tablecell .subtitle").removeClass("animated fadeInUp").css({ 'opacity': '0' });
            $(".hero-text-tablecell h1").removeClass("animated fadeInUp").css({ 'opacity': '0', 'animation-delay': '0.3s' });
            $(".hero-btns").removeClass("animated fadeInUp").css({ 'opacity': '0', 'animation-delay': '0.5s' });
        });

        $(".homepage-slider").on("translated.owl.carousel", function () {
            $(".hero-text-tablecell .subtitle").addClass("animated fadeInUp").css({ 'opacity': '0' });
            $(".hero-text-tablecell h1").addClass("animated fadeInUp").css({ 'opacity': '0', 'animation-delay': '0.3s' });
            $(".hero-btns").addClass("animated fadeInUp").css({ 'opacity': '0', 'animation-delay': '0.5s' });
        });


        // stikcy js
        $("#sticker").sticky({
            topSpacing: 0
        });

        //mean menu
        $('.main-menu').meanmenu({
            meanMenuContainer: '.mobile-menu',
            meanScreenWidth: "992"
        });

        // search form
        $(".search-bar-icon").on("click", function () {
            $(".search-area").addClass("search-active");
        });

        $(".close-btn").on("click", function () {
            $(".search-area").removeClass("search-active");
        });

    });


    jQuery(window).on("load", function () {
        jQuery(".loader").fadeOut(1000);
    });

    // Date of Deal of the month

    document.addEventListener("DOMContentLoaded", function () {
        const countdownElements = document.querySelectorAll("[data-countdown]");
        const loader = document.getElementById('loading-spinner');

        countdownElements.forEach(function (element) {
            const targetDate = new Date(element.getAttribute("data-countdown")).getTime();

            // Initialize and set up spans for each time unit
            function initializeCountdown() {
                element.innerHTML = `
              <div class="counter-column days">
                <div class="inner"><span class="count">00</span>Days</div>
              </div>
              <div class="counter-column hours">
                <div class="inner"><span class="count">00</span>Hours</div>
              </div>
              <div class="counter-column minutes">
                <div class="inner"><span class="count">00</span>Mins</div>
              </div>
              <div class="counter-column seconds">
                <div class="inner"><span class="count">00</span>Secs</div>
              </div>
            `;
                element.style.visibility = "visible";  // Show the countdown
                if (loader) loader.style.display = "none";  // Hide loader
            }

            function updateCountdown() {
                const now = new Date().getTime();
                const distance = targetDate - now;

                if (distance < 0) {
                    element.innerHTML = "<div>Deal Expired</div>";
                    return;
                }

                const days = Math.floor(distance / (1000 * 60 * 60 * 24));
                const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
                const seconds = Math.floor((distance % (1000 * 60)) / 1000);

                // Update only the numeric values without replacing the structure
                element.querySelector('.days .count').textContent = String(days).padStart(2, '0');
                element.querySelector('.hours .count').textContent = String(hours).padStart(2, '0');
                element.querySelector('.minutes .count').textContent = String(minutes).padStart(2, '0');
                element.querySelector('.seconds .count').textContent = String(seconds).padStart(2, '0');
            }

            initializeCountdown();  // Set up the initial HTML structure
            updateCountdown();      // Initial update
            setInterval(updateCountdown, 1000);  // Update every second
        });
    });




}(jQuery));

// ====================================================
// ====================================================

// (function ($) {
//     "use strict";

//     $(document).ready(function () {
//         // Testimonial Slider
//         $(".testimonial-sliders").owlCarousel({
//             items: 1,
//             loop: true,
//             autoplay: true,
//             autoplayTimeout: 5000,
//             smartSpeed: 800,
//             dots: true,
//             nav: false,
//         });

//         // Homepage Slider
//         $(".homepage-slider").owlCarousel({
//             items: 1,
//             loop: true,
//             autoplay: true,
//             autoplayTimeout: 7000,
//             smartSpeed: 1000,
//             nav: true,
//             dots: false,
//             navText: ['<i class="fas fa-angle-left"></i>', '<i class="fas fa-angle-right"></i>'],
//             responsive: {
//                 0: {
//                     items: 1,
//                     nav: false,
//                 },
//                 600: {
//                     items: 1,
//                     nav: true,
//                 },
//                 1000: {
//                     items: 1,
//                     nav: true,
//                 }
//             }
//         });

//         // Logo Carousel
//         $(".logo-carousel-inner").owlCarousel({
//             items: 4,
//             loop: true,
//             autoplay: true,
//             autoplayTimeout: 3000,
//             smartSpeed: 800,
//             margin: 30,
//             responsive: {
//                 0: {
//                     items: 1,
//                     nav: false,
//                 },
//                 600: {
//                     items: 3,
//                     nav: false,
//                 },
//                 1000: {
//                     items: 4,
//                     nav: false,
//                 }
//             }
//         });

//         // Countdown Timer
//         if ($('.time-countdown').length) {
//             $('.time-countdown').each(function () {
//                 var $this = $(this), finalDate = $(this).data('countdown');
//                 $this.countdown(finalDate, function (event) {
//                     $this.html(event.strftime(''
//                         + '<div class="counter-column"><div class="inner"><span class="count">%D</span> Days</div></div>'
//                         + '<div class="counter-column"><div class="inner"><span class="count">%H</span> Hours</div></div>'
//                         + '<div class="counter-column"><div class="inner"><span class="count">%M</span> Minutes</div></div>'
//                         + '<div class="counter-column"><div class="inner"><span class="count">%S</span> Seconds</div></div>'));
//                 });
//             });
//         }

//         // Isotope Product Filters
//         $(".product-filters li").on('click', function () {
//             $(".product-filters li").removeClass("active");
//             $(this).addClass("active");

//             var selector = $(this).attr('data-filter');
//             $(".product-lists").isotope({
//                 filter: selector,
//             });
//         });

//         $(".product-lists").isotope({
//             itemSelector: '.single-product-item',
//             layoutMode: 'fitRows',
//         });

//         // Magnific Popup for Video
//         $('.popup-youtube').magnificPopup({
//             disableOn: 700,
//             type: 'iframe',
//             mainClass: 'mfp-fade',
//             removalDelay: 160,
//             preloader: false,
//             fixedContentPos: false
//         });

//         // Magnific Popup for Image
//         $('.image-popup-vertical-fit').magnificPopup({
//             type: 'image',
//             closeOnContentClick: true,
//             mainClass: 'mfp-img-mobile',
//             image: {
//                 verticalFit: true
//             }
//         });

//         // Homepage Slider Animations
//         $(".homepage-slider").on("translate.owl.carousel", function () {
//             $(".hero-text-tablecell .subtitle").removeClass("fadeInUp").css({ 'opacity': '0' });
//             $(".hero-text-tablecell h1").removeClass("fadeInUp").css({ 'opacity': '0' });
//             $(".hero-btns").removeClass("fadeInUp").css({ 'opacity': '0' });
//         });

//         $(".homepage-slider").on("translated.owl.carousel", function () {
//             $(".hero-text-tablecell .subtitle").addClass("fadeInUp").css({ 'opacity': '1' });
//             $(".hero-text-tablecell h1").addClass("fadeInUp").css({ 'opacity': '1' });
//             $(".hero-btns").addClass("fadeInUp").css({ 'opacity': '1' });
//         });

//         // Sticky Header
//         $("#sticker").sticky({
//             topSpacing: 0,
//             zIndex: 9999
//         });

//         // Mobile Menu
//         $('.main-menu').meanmenu({
//             meanMenuContainer: '.mobile-menu',
//             meanScreenWidth: "992",
//         });

//         // Search Form Toggle
//         $(".search-bar-icon").on("click", function () {
//             $(".search-area").addClass("search-active");
//         });

//         $(".close-btn").on("click", function () {
//             $(".search-area").removeClass("search-active");
//         });

//         // Preloader
//         $(window).on("load", function () {
//             $(".loader").fadeOut(800);
//         });
//     });
// })(jQuery);
