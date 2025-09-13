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
     * Dynamically generates the FAQ accordion items from the `faqs` array.
     */
    function generateFaqs() {
        const faqContainer = document.getElementById('faq-container');
        if (!faqContainer) return;
        
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
     * Initializes all accordion items on the page.
     */
    function initializeAccordions() {
        const accordionButtons = document.querySelectorAll('.settings-toggle-btn');
        
        accordionButtons.forEach(button => {
            button.addEventListener('click', () => {
                const contentPanel = button.nextElementSibling;
                const isAlreadyActive = button.classList.contains('active');

                accordionButtons.forEach(otherButton => {
                    if (otherButton !== button) {
                        otherButton.classList.remove('active');
                        otherButton.nextElementSibling.style.maxHeight = null;
                    }
                });

                if (!isAlreadyActive) {
                    button.classList.add('active');
                    contentPanel.style.maxHeight = contentPanel.scrollHeight + "px";
                } else {
                    button.classList.remove('active');
                    contentPanel.style.maxHeight = null;
                }
            });
        });
    }
    
    // --- DEVELOPER CV DATA & FUNCTIONS ---

    // Store CV data in an object.
    const cvData = {
        christian: {
            fullName: "Christian V. Nolasco",
            role: "Documentation & Hardware Support", 
            imageSrc: "https://placehold.co/150x150/EFEFEF/333?text=CN",
            personal: {
                email: "nolascochristian66@gmail.com",
                phone: "09817955431",
                linkedin: "https://www.linkedin.com/in/christian-nolasco-504750366",
                github: null,
                facebook: "Christian Nolasco",
                address: "Purok 3, Barangay Fundado, Labo, Camarines Norte",
                birthday: "September 8, 2003",
                gender: "Male",
                religion: "Born Again"
            },
            summary: "I contribute in preparing documentation and provide support in finalizing IoT hardware design. In addition, I have hands-on experience in developing the RM Sole and Apparel Inventory System. My main skills include technical writing, and hardware integration support.",
            skills: [
                "Python (Basics)",
                "Java (Basics)",
                "C++ (Basics)",
                "Web Development (HTML, CSS, JavaScript)",
                "Prototyping",
                "Technical Documentation",
                "Research"
            ],
            experience: [
                { title: "Documentation Support, BSIT Academic Projects (2023–Present)", description: "Contributed to project documentation and supported the completion of IoT hardware design (e.g., Raspberry Pi case) for school projects." },
                { title: "Developer, RM Sole and Apparel Inventory system (2024)", description: "Developed the RM Sole and Apparel shop inventory management system." }
            ],
            education: {
                tertiary: "<strong>B.S. in Information Technology (Ongoing)</strong><br>Our Lady of Lourdes College Foundation (2022–Present)",
                secondary: "<strong>Senior High School (STEM)</strong><br>Mabini Colleges (2020–2022)<br><br><strong>Junior High School</strong><br>Camarines Norte College (2016–2020)",
                elementary: "<strong>Elementary</strong><br>L. Villamonte Elementary School (2010–2016)"
            }
        },
        clarence: {
            fullName: "Clarence P. Español",
            role: "Frontend Developer", 
            imageSrc: "https://placehold.co/150x150/EFEFEF/333?text=CE",
            personal: {
                email: "clarence.espanol0123@gmail.com",
                phone: "09286394903",
                linkedin: "https://www.linkedin.com/in/clarence-español-595742317",
                github: "https://github.com/ClarenceEspanol",
                facebook: null,
                address: "Purok 1B, Barangay Anahaw, Labo, Camarines Norte",
                birthday: "January 23, 2003",
                gender: "Male",
                religion: "Roman Catholic"
            },
            summary: "I contribute to the frontend optimization of the project, helping improve its functionality, usability, and overall user experience. I also assist in preparing documentation, provide support in finalizing IoT hardware design, and contribute as one of the researchers. In addition, I participated in prototyping and designing the user interface to ensure usability and visual consistency. I also have hands-on experience developing a full-stack e-commerce website with online database integration. My main skills include frontend web technologies, technical writing, prototyping, UI design, and hardware integration support.",
            skills: [
                "Python (Basics)",
                "Java (Basics)",
                "C++ (Basics)",
                "Web Development (HTML, CSS, JavaScript)",
                "Frontend Design",
                "Backend Development",
                "Online Database Integration",
                "Technical Documentation",
                "Prototyping",
                "UI/UX Design",
                "Research"
            ],
            experience: [
                { 
                    title: "Frontend Developer, Prototyping & Research Support, BSIT Academic Projects (2023–Present)", 
                    description: "Contributed to frontend optimization, UI design, prototyping, documentation, and assisted in finishing IoT hardware design (e.g., Raspberry Pi case) while serving as one of the researchers in school projects." 
                },
                { 
                    title: "Full-Stack Developer, JBC School Supplies & Hardware E-Commerce Website (2024)", 
                    description: "Developed both the frontend and backend of an e-commerce website with online database integration. Website: https://jbcstore2009.web.app" 
                }
            ],
            education: {
                tertiary: "<strong>B.S. in Information Technology (Ongoing)</strong><br>Our Lady of Lourdes College Foundation (2022–Present)",
                secondary: "<strong>Senior High School (GAS)</strong><br>Our Lady of Lourdes College Foundation (2020–2022)<br><br><strong>Junior High School</strong><br>St. John the Apostle Academy (2016–2020)",
                elementary: "<strong>Elementary</strong><br>Daet Elementary School (2010–2016)"
            }
        },
        christianLuis: {
            fullName: "Christian Luis S. Aceron",
            role: "Backend Developer & Data Scientist",
            imageSrc: "https://placehold.co/150x150/EFEFEF/333?text=CA",
            personal: {
                email: "christianluis.aceron@gmail.com",
                phone: "09519712807",
                linkedin: "https://www.linkedin.com/in/christianluisaceron/",
                github: "https://github.com/aceaceron",
                facebook: "https://www.facebook.com/christianluisaceron",
                address: "Purok 2, Brgy. Kalamunding, Labo, Camarines Norte",
                birthday: "October 22, 2004",
                gender: "Male",
                religion: "Roman Catholic"
            },
            summary: "I contribute to some of the frontend and the full backend of the project, implementing machine learning, database, sensor calibration and other core function of the project, making the project possible and able to be used.",
            skills: [
                "Python",
                "Java (Basics)",
                "C++ (Basics)",
                "Web Development (HTML, CSS, JavaScript, PHP)",
                "Database Implementation (MySQL, Firebase, SQLite)"
            ],
            experience: [
                { title: "Full Stack Developer, Data Scientist, BSIT Academic Projects (2022–Present)", description: "Contributed full stack web app of BantayTubig, frontend, backend, machine learning, database implementation." },
                { title: "Full Stack Developer", description: "Developed Transient House Management System as a Requirement for System Integration and Architecture Subject." }
            ],
            education: {
                tertiary: "<strong>B.S. in Information Technology</strong><br>Our Lady of Lourdes College Foundation (2022-2026)",
                secondary: "<strong>Senior High School (STEM)</strong><br>Camarines Norte College (2020-2022)<br><br><strong>Junior High School</strong><br>Camarines Norte College (2016-2020)",
                elementary: "<strong>Elementary</strong><br>Labo Elementary School (2010-2016)"
            }
        }
    };

    // This function generates the developer cards from the cvData object
    function populateDeveloperCards() {
        const container = document.querySelector('.developers-container');
        if (!container) return; // Safety check

        container.innerHTML = ''; // Clear any existing cards

        for (const devKey in cvData) {
            const dev = cvData[devKey];
            const cardHTML = `
                <div class="dev-card" data-dev="${devKey}">
                    <img src="${dev.imageSrc}" alt="Developer ${dev.fullName}">
                    <h3>${dev.fullName}</h3>
                    <p>${dev.role}</p>
                </div>
            `;
            container.innerHTML += cardHTML;
        }
    }

    /**
     * Initializes all logic for the CV modal.
     * This should only be called AFTER populateDeveloperCards() has run.
     */
    function initializeDeveloperModals() {
        const devCards = document.querySelectorAll('.dev-card'); // Now this finds the cards
        const cvModal = document.getElementById('cvModal');
        const cvModalHeader = document.querySelector('#cvModal .modal-header');
        const cvModalBody = document.getElementById('cvModalBody');

        const emailIcon = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path><polyline points="22,6 12,13 2,6"></polyline></svg>`;
        const phoneIcon = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path></svg>`;
        const facebookIcon = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"></path></svg>`;
        const githubIcon = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"></path></svg>`;
        const linkedinIcon = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"></path><rect x="2" y="9" width="4" height="12"></rect><circle cx="4" cy="4" r="2"></circle></svg>`;

        // Setup open-modal listeners
        devCards.forEach(card => {
            card.addEventListener('click', () => {
                const devId = card.dataset.dev;
                const data = cvData[devId];

                if (data) {
                    cvModalHeader.innerHTML = `
                        <div class="cv-header-content">
                            <img src="${data.imageSrc}" alt="Profile picture of ${data.fullName}" class="cv-profile-pic">
                            <h2 class="cv-modal-title">About ${data.fullName}</h2>
                        </div>
                        <button id="closeCvModalBtn" class="modal-close-btn">&times;</button>
                    `;
                    
                    cvModalBody.innerHTML = `
                        <div class="cv-section cv-contact-info">
                            <div class="cv-contact-icons">
                                ${data.personal.email ? `<a href="mailto:${data.personal.email}" target="_blank" title="Email">${emailIcon}</a>` : ''}
                                ${data.personal.phone ? `<a href="tel:${data.personal.phone}" target="_blank" title="Phone">${phoneIcon}</a>` : ''}
                                ${data.personal.linkedin ? `<a href="${data.personal.linkedin}" target="_blank" title="LinkedIn">${linkedinIcon}</a>` : ''}
                                ${data.personal.github ? `<a href="${data.personal.github}" target="_blank" title="GitHub">${githubIcon}</a>` : ''}
                                ${data.personal.facebook ? `<a href="${data.personal.facebook}" target="_blank" title="Facebook">${facebookIcon}</a>` : ''}
                            </div>
                            <p><strong>Address:</strong> ${data.personal.address || 'N/A'}</p>
                            <p><strong>Birthday:</strong> ${data.personal.birthday || 'N/A'}</p>
                            <p><strong>Gender:</strong> ${data.personal.gender || 'N/A'}</p>
                            <p><strong>Religious Affiliation:</strong> ${data.personal.religion || 'N/A'}</p>
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
                        ${data.experience && data.experience.length > 0 ? `
                        <div class="cv-section">
                            <h4>Experience</h4>
                            ${data.experience.map(exp => `<p><strong>${exp.title}</strong><br>${exp.description}</p>`).join('')}
                        </div>
                        ` : ''}
                        <div class="cv-section">
                            <h4>Education</h4>
                            <p><strong>Tertiary:</strong><br>${data.education.tertiary}</p>
                            <p><strong>Secondary:</strong><br>${data.education.secondary}</p>
                            <p><strong>Elementary:</strong><br>${data.education.elementary}</p>
                        </div>
                    `;
                    
                    cvModal.style.display = 'flex';
                    
                    document.getElementById('closeCvModalBtn').addEventListener('click', closeModal);
                }
            });
        });

        // Setup close-modal listeners
        const closeModal = () => {
            if(cvModal) cvModal.style.display = 'none';
        };

        // This listener is for the original close button that exists on page load
        const initialCloseBtn = document.getElementById('closeCvModalBtn');
        if (initialCloseBtn) {
            initialCloseBtn.addEventListener('click', closeModal);
        }

        if (cvModal) {
            cvModal.addEventListener('click', (event) => {
                if (event.target === cvModal) {
                    closeModal();
                }
            });
        }
    }
    
    // --- PAGE INITIALIZATION (Corrected Order) ---
    generateFaqs();
    initializeAccordions();
    populateDeveloperCards();      // First, create the developer cards in the HTML.
    initializeDeveloperModals();   // Second, find those new cards and make them clickable.
});