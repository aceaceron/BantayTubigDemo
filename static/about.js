// static/about.js

/**
 * ------------------------------------------------------------------------
 * UNIVERSAL SIDEBAR & HEADER SCRIPT
 * ------------------------------------------------------------------------
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

document.addEventListener('DOMContentLoaded', function() {

    // --- FAQ Data ---
    // Storing the FAQ content in JavaScript makes it easy to update without touching HTML.
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

    
    // --- Accordion Logic ---
    const faqContainer = document.getElementById('faq-container');
    
    const accordionHeaders = document.querySelectorAll('.accordion-header');
    accordionHeaders.forEach(header => {
        header.addEventListener('click', () => {
            // Close other open accordions
            accordionHeaders.forEach(otherHeader => {
                if (otherHeader !== header && otherHeader.classList.contains('active')) {
                    otherHeader.classList.remove('active');
                    otherHeader.nextElementSibling.style.maxHeight = null;
                    otherHeader.nextElementSibling.style.padding = "0 20px";
                }
            });

            // Toggle the clicked accordion
            header.classList.toggle('active');
            const content = header.nextElementSibling;
            if (content.style.maxHeight) {
                content.style.maxHeight = null;
                content.style.padding = "0 20px";
            } else {
                content.style.maxHeight = content.scrollHeight + 40 + "px";
                content.style.padding = "20px";
            }
        });
    });
    
    // Function to generate the FAQ accordion from the data
    function generateFaqs() {
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
     * Initializes all accordions on the page with one-at-a-time toggle behavior.
     */
    function initializeAccordions() {
        const accordionButtons = document.querySelectorAll('.settings-toggle-btn');
        
        accordionButtons.forEach(button => {
            button.addEventListener('click', () => {
                const contentPanel = button.nextElementSibling;
                const isAlreadyActive = button.classList.contains('active');

                // First, close all other accordion items
                accordionButtons.forEach(otherButton => {
                    if (otherButton !== button) {
                        otherButton.classList.remove('active');
                        otherButton.nextElementSibling.style.maxHeight = null;
                    }
                });

                // Then, toggle the clicked item
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
    // --- Developer CV Modal Logic ---
    const devCards = document.querySelectorAll('.dev-card');
    const cvModal = document.getElementById('cvModal');
    const closeCvModalBtn = document.getElementById('closeCvModalBtn');
    const cvModalTitle = document.getElementById('cvModalTitle');
    const cvModalBody = document.getElementById('cvModalBody');

    // Store CV data in an object for easy access
    const cvData = {
        alex: {
            name: "Alex Reyes's CV",
            content: `
                <h4>Summary</h4>
                <p>A dedicated and innovative System Architect with over 10 years of experience in designing and implementing scalable, high-performance systems. Specializes in IoT architecture, database management, and leading development teams from concept to deployment.</p>
                <h4>Skills</h4>
                <ul>
                    <li>System Architecture & Design</li>
                    <li>Python (Flask), C++, Embedded Systems</li>
                    <li>Database Management (SQLite, PostgreSQL)</li>
                    <li>IoT Protocols (MQTT, CoAP)</li>
                    <li>Agile Project Management</li>
                </ul>
                <h4>Experience</h4>
                <p><strong>Lead Developer, BantayTubig Project (2023-Present)</strong><br>Architected the end-to-end system, from sensor integration to cloud-based data processing and visualization.</p>
                <p><strong>Senior Software Engineer, TechSolutions Inc. (2018-2023)</strong><br>Led the development of a large-scale logistics management platform.</p>
                <h4>Education</h4>
                <p><strong>B.S. in Computer Engineering</strong><br>University of the Philippines Diliman</p>
            `
        },
        maria: {
            name: "Maria Santos's CV",
            content: `
                <h4>Summary</h4>
                <p>A creative and detail-oriented UI/UX Designer and Frontend Developer with a passion for building intuitive and user-friendly interfaces. Proficient in modern web technologies and user-centered design principles.</p>
                <h4>Skills</h4>
                <ul>
                    <li>UI/UX Design (Figma, Adobe XD)</li>
                    <li>HTML5, CSS3, JavaScript (ES6+)</li>
                    <li>Frontend Frameworks (React, Vue.js)</li>
                    <li>Responsive Web Design</li>
                    <li>User Research & Prototyping</li>
                </ul>
                <h4>Experience</h4>
                <p><strong>UI/UX Designer, BantayTubig Project (2023-Present)</strong><br>Designed the complete user interface and developed the frontend application, ensuring a seamless and intuitive user experience across all devices.</p>
                <p><strong>Frontend Developer, CreativeWeb Co. (2020-2023)</strong><br>Developed and maintained responsive websites and web applications for various clients.</p>
                <h4>Education</h4>
                <p><strong>B.S. in Information Technology</strong><br>Ateneo de Manila University</p>
            `
        },
        kenji: {
            name: "Kenji Tanaka's CV",
            content: `
                <h4>Summary</h4>
                <p>A proficient Backend and Database Engineer with a strong background in data modeling, API development, and ensuring data integrity and performance. Experienced in building robust server-side logic and managing complex databases.</p>
                <h4>Skills</h4>
                <ul>
                    <li>Backend Development (Python, Node.js)</li>
                    <li>RESTful API Design</li>
                    <li>Database Administration (SQLite, MySQL)</li>
                    <li>Data Security & Optimization</li>
                    <li>Linux Server Management</li>
                </ul>
                <h4>Experience</h4>
                <p><strong>Backend Engineer, BantayTubig Project (2023-Present)</strong><br>Developed the entire backend infrastructure, including the Flask API, database schema, and real-time data handling logic.</p>
                <p><strong>Database Administrator, DataCorp PH (2019-2023)</strong><br>Managed and optimized large-scale databases for enterprise clients.</p>
                <h4>Education</h4>
                <p><strong>B.S. in Computer Science</strong><br>De La Salle University</p>
            `
        }
    };

    // Add click listeners to each developer card
    devCards.forEach(card => {
        card.addEventListener('click', () => {
            const devId = card.dataset.dev;
            const data = cvData[devId];

            if (data) {
                cvModalTitle.textContent = data.name;
                cvModalBody.innerHTML = data.content;
                cvModal.style.display = 'flex';
            }
        });
    });

    // Close the modal
    const closeModal = () => {
        cvModal.style.display = 'none';
    };

    closeCvModalBtn.addEventListener('click', closeModal);
    cvModal.addEventListener('click', (event) => {
        if (event.target === cvModal) {
            closeModal();
        }
    });

    
    // --- INITIALIZATION ---
    generateFaqs();
    initializeAccordions();
});
