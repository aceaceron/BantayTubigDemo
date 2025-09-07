// static/about.js

/**
 * ========================================================================
 * UNIVERSAL SIDEBAR SCRIPT
 * Manages the slide-out navigation menu, present on all pages.
 * ========================================================================
 */
function setupGlobalNavigation() {
    const sidebar = document.getElementById('sidebarMenu');
    const menuIcon = document.querySelector('.menu-icon');
    
    menuIcon.addEventListener('click', (event) => {
        event.stopPropagation();
        sidebar.classList.toggle('open');
        if (window.innerWidth <= 992) {
            menuIcon.classList.toggle('active');
            menuIcon.innerHTML = menuIcon.classList.contains('active') ? "&#10006;" : "&#9776;";
        }
    });

    document.addEventListener('click', (event) => {
        if (!sidebar.contains(event.target) && !menuIcon.contains(event.target)) {
            sidebar.classList.remove('open');
            if (window.innerWidth <= 992 && menuIcon.classList.contains('active')) {
                menuIcon.classList.remove('active');
                menuIcon.innerHTML = "&#9776;";
            }
        }
    });
}

/**
 * ========================================================================
 * MAIN EXECUTION BLOCK
 * This is the primary function that runs after the entire HTML page
 * has been loaded and is ready (thanks to 'DOMContentLoaded').
 * ========================================================================
 */
document.addEventListener('DOMContentLoaded', function() {

    // --- INITIALIZE GLOBAL COMPONENTS ---
    setupGlobalNavigation();
    
    // --- FAQ DATA ---
    // Storing the FAQ content in a JavaScript array of objects separates the data from the presentation (HTML).
    // This makes it easy to add, remove, or edit FAQs without modifying the HTML file directly.
    const faqs = [
        {
            question: "How do I check the current water quality?",
            answer: "The main <strong>Dashboard</strong> provides a real-time overview of the water quality, including the current classification (Good, Average, Poor, Bad) and live sensor readings."
        },
        {
            question: "What do the different quality levels mean?",
            answer: "The quality levels are determined by comparing sensor readings to pre-defined thresholds. You can view and edit these thresholds on the <strong>Alerts & Notification > Thresholds</strong> page."
        },
        {
            question: "How can I export a report of the data?",
            answer: "Navigate to the <strong>Analytics & Reports</strong> page. Use the date and time pickers to select your desired range, then click the 'Export as PDF' or 'Export as CSV' buttons to download the report."
        },
        {
            question: "How do I calibrate a sensor?",
            answer: "Go to the <strong>Device & Sensor</strong> page. In the 'Sensor Status & Calibration' card, find the sensor you wish to calibrate and click the 'Calibrate' button to launch the guided calibration wizard."
        },
        {
            question: "How do I change my password?",
            answer: "You can change your password on the <strong>System Settings</strong> page under the 'Security' section. You will need to enter your current password to set a new one."
        },
        {
            question: "What is TDS and Turbidity?",
            answer: "<strong>TDS (Total Dissolved Solids)</strong> measures the total amount of dissolved substances in the water, typically measured in parts per million (ppm). <strong>Turbidity</strong> measures the cloudiness or haziness of the water caused by suspended particles, measured in Nephelometric Turbidity Units (NTU)."
        }
    ];

    /**
     * Dynamically generates the FAQ accordion items from the `faqs` array and injects them into the page.
     * How it works:
     * 1. Grabs the placeholder container `#faq-container` from the DOM.
     * 2. Loops through each object in the `faqs` array using `forEach`.
     * 3. For each FAQ, it constructs an HTML string for an accordion item using a template literal.
     * 4. It appends this string to a variable `faqHtml`.
     * 5. After the loop, it sets the `innerHTML` of the container to the complete `faqHtml` string,
     * which causes the browser to parse and render all the new FAQ elements at once.
     */
    function generateFaqs() {
        const faqContainer = document.getElementById('faq-container');
        if (!faqContainer) return; // Exit if the container element doesn't exist
        
        let faqHtml = '';
        faqs.forEach(faq => {
            faqHtml += `
                <div class="settings-accordion-item">
                    <button class="settings-toggle-btn">${faq.question}<span class="arrow-icon">▼</span></button>
                    <div class="settings-content-panel">
                        <div class="content-card-inner">
                            <p>${faq.answer}</p>
                        </div>
                    </div>
                </div>
            `;
        });
        faqContainer.innerHTML = faqHtml;
    }

    /**
     * Initializes all accordion items on the page (both static and dynamically generated).
     * This logic ensures that only one accordion item can be open at a time.
     * How it works:
     * 1. Selects all accordion buttons (`.settings-toggle-btn`).
     * 2. Attaches a `click` event listener to each button.
     * 3. When a button is clicked:
     * a. It first loops through ALL accordion buttons to close any that are currently open
     * by removing the 'active' class and setting their panel's `maxHeight` to `null`.
     * b. It then checks if the clicked item was already open.
     * c. If it was NOT open, it opens it by adding the 'active' class and setting the panel's `maxHeight`
     * to its `scrollHeight`. The `scrollHeight` is the full height of the content, allowing for a smooth
     * CSS transition that expands the panel to reveal its contents.
     */
    function initializeAccordions() {
        const accordionButtons = document.querySelectorAll('.settings-toggle-btn');
        
        accordionButtons.forEach(button => {
            button.addEventListener('click', () => {
                const contentPanel = button.nextElementSibling;
                const isAlreadyActive = button.classList.contains('active');

                // First, close all other open accordion items.
                accordionButtons.forEach(otherButton => {
                    if (otherButton !== button) {
                        otherButton.classList.remove('active');
                        otherButton.nextElementSibling.style.maxHeight = null;
                    }
                });

                // Then, toggle the clicked item.
                if (!isAlreadyActive) {
                    button.classList.add('active');
                    contentPanel.style.maxHeight = contentPanel.scrollHeight + "px"; // Open it
                } else {
                    button.classList.remove('active');
                    contentPanel.style.maxHeight = null; // Close it (already handled by loop above, but good practice)
                }
            });
        });
    }
    
    // --- DEVELOPER CV MODAL LOGIC ---
    // This section handles the functionality for the developer CV popup.

    // --- Developer CV Modal Logic ---
    const devCards = document.querySelectorAll('.dev-card');
    const cvModal = document.getElementById('cvModal');
    const closeCvModalBtn = document.getElementById('closeCvModalBtn');
    const cvModalHeader = document.querySelector('#cvModal .modal-header'); // Target the header container
    const cvModalBody = document.getElementById('cvModalBody');

    // --- SVG Icons ---
    // Storing SVGs in variables makes the code cleaner.
    const emailIcon = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path><polyline points="22,6 12,13 2,6"></polyline></svg>`;
    const phoneIcon = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path></svg>`;
    const facebookIcon = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"></path></svg>`;
    const githubIcon = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"></path></svg>`;
    const linkedinIcon = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"></path><rect x="2" y="9" width="4" height="12"></rect><circle cx="4" cy="4" r="2"></circle></svg>`;

    // Store CV data in an object. The keys ('alex', 'maria', 'kenji') directly match the
    // 'data-dev' attribute values in the HTML, creating an easy link between the element and its data.
    const cvData = {
        alex: {
            fullName: "Alex Reyes",
            imageSrc: "https://placehold.co/150x150/EFEFEF/333?text=AR",
            // imageSrc: "/static/images/alex-reyes.jpg",
            personal: {
                email: "alex.reyes@bantaytubig.ph",
                phone: "+639171234567",
                linkedin: "https://linkedin.com/in/alexreyes", 
                github: "https://github.com/alexreyes",     
                facebook: "https://facebook.com/alexreyes",
                address: "123 Aqua St., Brgy. Poblacion, Jose Panganiban",
                birthday: "January 15, 1990",
                gender: "Male",
                religion: "Roman Catholic"
            },
            summary: "A dedicated and innovative System Architect with over 10 years of experience in designing and implementing scalable, high-performance systems. Specializes in IoT architecture, database management, and leading development teams from concept to deployment.",
            skills: [
                "System Architecture & Design", "Python (Flask), C++, Embedded Systems", "Database Management (SQLite, PostgreSQL)", "IoT Protocols (MQTT, CoAP)", "Agile Project Management"
            ],
            experience: [
                { title: "Lead Developer, BantayTubig Project (2023-Present)", description: "Architected the end-to-end system, from sensor integration to cloud-based data processing and visualization." },
                { title: "Senior Software Engineer, TechSolutions Inc. (2018-2023)", description: "Led the development of a large-scale logistics management platform." }
            ],
            education: {
                tertiary: "<strong>B.S. in Computer Engineering</strong><br>University of the Philippines Diliman (2007-2012)",
                secondary: "<strong>Philippine Science High School</strong><br>Bicol Region Campus (2003-2007)",
                elementary: "<strong>Jose Panganiban Elementary School</strong><br>Graduated with Honors (1997-2003)"
            }
        },
        maria: {
            fullName: "Maria Santos",
            imageSrc: "https://placehold.co/150x150/EFEFEF/333?text=MS",
            // imageSrc: "/static/images/maria-santos.png",
            personal: {
                email: "maria.santos@bantaytubig.ph",
                phone: "+639181234567",
                linkedin: "https://linkedin.com/in/mariasantos", 
                github: null,
                facebook: "https://facebook.com/mariasantos",
                address: "456 Coral Rd., Brgy. Plaridel, Jose Panganiban",
                birthday: "June 22, 1994",
                gender: "Female",
                religion: "Born-Again Christian"
            },
            summary: "A creative and detail-oriented UI/UX Designer and Frontend Developer with a passion for building intuitive and user-friendly interfaces. Proficient in modern web technologies and user-centered design principles.",
            skills: [
                "UI/UX Design (Figma, Adobe XD)",
                "HTML5, CSS3, JavaScript (ES6+)",
                "Frontend Frameworks (React, Vue.js)",
                "Responsive Web Design",
                "User Research & Prototyping"
            ],
            experience: [
                { title: "UI/UX Designer, BantayTubig Project (2023-Present)", description: "Designed the complete user interface and developed the frontend application, ensuring a seamless and intuitive user experience across all devices." },
                { title: "Frontend Developer, CreativeWeb Co. (2020-2023)", description: "Developed and maintained responsive websites and web applications for various clients." }
            ],
            education: {
                tertiary: "<strong>B.S. in Information Technology</strong><br>Ateneo de Manila University (2011-2015)",
                secondary: "<strong>La Consolacion College - Daet</strong><br>Graduated with High Honors (2007-2011)",
                elementary: "<strong>St. Raphael Academy</strong><br>Graduated Valedictorian (2001-2007)"
            }
        },
        kenji: {
            fullName: "Kenji Tanaka",
            imageSrc: "https://placehold.co/150x150/EFEFEF/333?text=KT",
            // imageSrc: "/static/images/kenji-tanaka.jpg",
            personal: {
                email: "kenji.tanaka@bantaytubig.ph",
                phone: "+639191234567",
                linkedin: null, 
                github: null,
                facebook: "https://facebook.com/kenjitanaka",
                address: "789 Pearl Blvd., Brgy. Bagongbayan, Jose Panganiban",
                birthday: "November 3, 1992",
                gender: "Male",
                religion: "Aglipayan"
            },
            summary: "A proficient Backend and Database Engineer with a strong background in data modeling, API development, and ensuring data integrity and performance. Experienced in building robust server-side logic and managing complex databases.",
            skills: [
                "Backend Development (Python, Node.js)",
                "RESTful API Design",
                "Database Administration (SQLite, MySQL)",
                "Data Security & Optimization",
                "Linux Server Management"
            ],
            experience: [],
            education: {
                tertiary: "<strong>B.S. in Computer Science</strong><br>De La Salle University (2009-2014)",
                secondary: "<strong>Mabini Colleges, Inc.</strong><br>Graduated with Honors (2005-2009)",
                elementary: "<strong>Camarines Norte State College - Abaño Campus</strong><br>Graduated Salutatorian (1999-2005)"
            }
        }
    };
/**
     * Sets up the event listeners to open the modal.
     * How it works:
     * 1. It iterates over each developer card (`.dev-card`).
     * 2. For each card, it adds a `click` event listener.
     * 3. When a card is clicked:
     * a. It reads the developer's ID from the `data-dev` attribute (e.g., `card.dataset.dev` gives "alex").
     * b. It uses this ID to look up the corresponding developer's information in the `cvData` object.
     * c. It populates the modal's title and body with the retrieved data.
     * d. It makes the modal visible by changing its CSS `display` property to `flex`.
     */
    devCards.forEach(card => {
        card.addEventListener('click', () => {
            const devId = card.dataset.dev;
            const data = cvData[devId];

            if (data) {
                // --- 1. Build the new Header ---
                cvModalHeader.innerHTML = `
                    <div class="cv-header-content">
                        <img src="${data.imageSrc}" alt="Profile picture of ${data.fullName}" class="cv-profile-pic">
                        <h2 class="cv-modal-title">About ${data.fullName}</h2>
                    </div>
                    <button id="closeCvModalBtn" class="modal-close-btn">&times;</button>
                `;
                
                // --- 2. Build the new Body ---
                cvModalBody.innerHTML = `
                    <div class="cv-section cv-contact-info">
                        <div class="cv-contact-icons">
                            ${data.personal.email ? `<a href="mailto:${data.personal.email}" target="_blank" title="Email">${emailIcon}</a>` : ''}
                            ${data.personal.phone ? `<a href="tel:${data.personal.phone}" target="_blank" title="Phone">${phoneIcon}</a>` : ''}
                            ${data.personal.linkedin ? `<a href="${data.personal.linkedin}" target="_blank" title="LinkedIn">${linkedinIcon}</a>` : ''}
                            ${data.personal.github ? `<a href="${data.personal.github}" target="_blank" title="GitHub">${githubIcon}</a>` : ''}
                            ${data.personal.facebook ? `<a href="${data.personal.facebook}" target="_blank" title="Facebook">${facebookIcon}</a>` : ''}
                        </div>
                        <p><strong>Address:</strong> ${data.personal.address}</p>
                        <p><strong>Birthday:</strong> ${data.personal.birthday}</p>
                        <p><strong>Gender:</strong> ${data.personal.gender}</p>
                        <p><strong>Religious Affiliation:</strong> ${data.personal.religion}</p>
                    </div>


                    <div class="cv-section">
                        <h4>Summary</h4>
                        <p>${data.summary}</p>
                    </div>

                    <div class="cv-section">
                        <h4>Skills</h4>
                        <ul>
                            ${data.skills.map(skill => `<li>${skill}</li>`).join('')}
                        </ul>
                    </div>

                    ${/* --- START CONDITIONAL BLOCK --- */''}
                    ${data.experience && data.experience.length > 0 ? `
                    <div class="cv-section">
                        <h4>Experience</h4>
                        ${data.experience.map(exp => `<p><strong>${exp.title}</strong><br>${exp.description}</p>`).join('')}
                    </div>
                    ` : ''}
                    ${/* --- END CONDITIONAL BLOCK --- */''}

                    <div class="cv-section">
                        <h4>Education</h4>
                        <p><strong>Tertiary:</strong><br>${data.education.tertiary}</p>
                        <p><strong>Secondary:</strong><br>${data.education.secondary}</p>
                        <p><strong>Elementary:</strong><br>${data.education.elementary}</p>
                    </div>
                `;
                
                // --- 3. Show the Modal ---
                cvModal.style.display = 'flex';
                
                // Re-add event listener to the new close button
                // This is important because we replaced the button's HTML.
                document.getElementById('closeCvModalBtn').addEventListener('click', closeModal);
            }
        });
    });

    /**
     * Function and event listeners to close the modal.
     * How it works:
     * 1. A reusable `closeModal` function is defined to hide the modal by setting its `display` to `none`.
     * 2. This function is attached to two events for user convenience:
     * a. A click on the 'X' button (`#closeCvModalBtn`).
     * b. A click on the modal overlay itself. The `if (event.target === cvModal)` check ensures
     * this only triggers when clicking the gray background, not the content panel inside it.
     */
    const closeModal = () => {
        cvModal.style.display = 'none';
    };

    closeCvModalBtn.addEventListener('click', closeModal);
    cvModal.addEventListener('click', (event) => {
        if (event.target === cvModal) {
            closeModal();
        }
    });

    
    // --- PAGE INITIALIZATION ---
    // These functions are called at the end to set up the page after the DOM is ready.
    generateFaqs();         // Creates the FAQ items from the data array.
    initializeAccordions(); // Attaches the interactive open/close logic to all accordion items.
});
