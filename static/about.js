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
        // General & Getting Started
        {
            category: "General & Getting Started",
            question: "Ano ang BantayTubig system? <span class='english-translation'>What is the BantayTubig system?</span>",
            answer: "Ang BantayTubig system ay isang smart water quality monitoring solution na nagbibigay ng real-time data at analytics para makatulong sa inyo na masiguro na malinis at safe ang tubig. <span class='english-translation'>The BantayTubig system is a smart water quality monitoring solution that provides real-time data and analytics to help you ensure water is clean and safe.</span>"
        },
        {
            category: "General & Getting Started",
            question: "Paano ako mag-log in sa system? <span class='english-translation'>How do I log in to the system?</span>",
            answer: "Pwede kayong mag-log in sa pamamagitan ng pagbisita sa <strong>Login</strong> page at pag-enter ng inyong registered email at password. <span class='english-translation'>You can log in by visiting the <strong>Login</strong> page and entering your registered email and password.</span>"
        },
        {
            category: "General & Getting Started",
            question: "Nakalimutan ko ang password ko. Paano ko ito i-reset? <span class='english-translation'>I forgot my password. How do I reset it?</span>",
            answer: "Kung ikaw ay isang <strong>Admin</strong>, maaari mong gamitin ang 'Forgot Password' link sa <strong>Login</strong> page upang i-reset ang iyong password. Para sa mga hindi admin na user, mangyaring makipag-ugnayan sa inyong Administrator kung nakalimutan ninyo ang inyong password. <span class='english-translation'>If you are an <strong>Admin</strong>, you can use the 'Forgot Password' link on the <strong>Login</strong> page to reset your password. For non-admin users, please contact your Administrator if you have forgotten your password.</span>"
        },
        {
            category: "General & Getting Started",
            question: "Ano ang dapat kong gawin kung sinasabi ng system na walang network connection? <span class='english-translation'>What should I do if the system says there is no network connection?</span>",
            answer: "May lalabas na banner sa baba ng page na nagsasabi ng 'No network connection' at na ang data na pinapakita ay hindi live. I-check ang inyong internet connection at ang connectivity ng device. <span class='english-translation'>A banner will appear at the bottom of the page indicating 'No network connection' and that displayed data may not be live. Check your internet connection and the device's connectivity.</span>"
        },
        {
            category: "General & Getting Started",
            question: "Paano ko i-configure ang network connection ng device ko? <span class='english-translation'>How do I configure my device's network connection?</span>",
            answer: "Pwede mong i-connect ang device sa isang local network o WiFi gamit ang <strong>BantayTubig Setup</strong> page. <span class='english-translation'>You can connect the device to a local network or WiFi using the <strong>BantayTubig Setup</strong> page.</span>"
        },
        
        // Dashboard
        {
            category: "Dashboard",
            question: "Paano ko i-check ang kasalukuyang water quality? <span class='english-translation'>How do I check the current water quality?</span>",
            answer: "Ang main <strong>Dashboard</strong> ay nagbibigay ng real-time overview ng water quality, kasama ang kasalukuyang classification (Good, Average, Poor, Bad) at live sensor readings. <span class='english-translation'>The main <strong>Dashboard</strong> provides a real-time overview of the water quality, including the current classification (Good, Average, Poor, Bad) and live sensor readings.</span>"
        },
        
        // Analytics & Reports
        {
            category: "Analytics & Reports",
            question: "Paano ako mag-export ng report ng data? <span class='english-translation'>How can I export a report of the data?</span>",
            answer: "Mag-navigate sa <strong>Analytics & Reports</strong> page. Gamitin ang date and time pickers para pumili ng inyong gustong range, tapos i-click ang 'Export as PDF' o 'Export as CSV' buttons para i-download ang report. <span class='english-translation'>Navigate to the <strong>Analytics & Reports</strong> page. Use the date and time pickers to select your desired range, then click the 'Export as PDF' or 'Export as CSV' buttons to download the report.</span>"
        },
        {
            category: "Analytics & Reports",
            question: "Para saan ang primary date range filter? <span class='english-translation'>What is the primary date range filter used for?</span>",
            answer: "Ang <strong>Primary Date Range</strong> filter sa <strong>Analytics & Reports</strong> page ay nagpapahintulot sa inyo na pumili ng isang specific na period kung saan gusto ninyong makita at i-analyze ang data. <span class='english-translation'>The <strong>Primary Date Range</strong> filter on the <strong>Analytics & Reports</strong> page allows you to select a specific period for which you want to view and analyze data.</span>"
        },
        {
            category: "Analytics & Reports",
            question: "Pwede ba akong mag-compare ng data mula sa dalawang magkaibang time periods? <span class='english-translation'>Can I compare data from two different time periods?</span>",
            answer: "Oo, sa <strong>Analytics & Reports</strong> page, pwede ninyong gamitin ang <strong>Comparison Date Range (Optional)</strong> filter para pumili ng pangalawang time period para sa comparison. <span class='english-translation'>Yes, on the <strong>Analytics & Reports</strong> page, you can use the <strong>Comparison Date Range (Optional)</strong> filter to select a second time period for comparison.</span>"
        },
        {
            category: "Analytics & Reports",
            question: "Paano ko makikita ang data para sa isang specific na oras ng araw? <span class='english-translation'>How can I view data for a specific time of day?</span>",
            answer: "Ang <strong>Analytics & Reports</strong> page ay nagbibigay ng optional na <strong>Hourly Range</strong> filter, na nagpapahintulot sa inyo na mag-specify ng start at end time para sa inyong analysis. <span class='english-translation'>The <strong>Analytics & Reports</strong> page provides an optional <strong>Hourly Range</strong> filter, allowing you to specify a start and end time for your analysis.</span>"
        },
        {
            category: "Analytics & Reports",
            question: "Paano ko ma-aadjust ang data granularity sa reports? <span class='english-translation'>How can I adjust the data granularity in reports?</span>",
            answer: "Sa <strong>Analytics & Reports</strong> page, pwede mong i-select ang <strong>Data Interval</strong> sa minutes para i-adjust ang granularity ng data na pinapakita sa charts at reports. <span class='english-translation'>On the <strong>Analytics & Reports</strong> page, you can select the <strong>Data Interval</strong> in minutes to adjust the granularity of the data displayed on charts and in reports.</span>"
        },
        
        // Alerts & Notification
        {
            category: "Alerts & Notification",
            question: "Ano ang ibig sabihin ng iba't ibang quality levels? <span class='english-translation'>What do the different quality levels mean?</span>",
            answer: "Ang quality levels ay tinutukoy sa pamamagitan ng pag-compare ng sensor readings sa pre-defined thresholds. Pwede mong makita at i-edit ang mga thresholds na ito sa <strong>Alerts & Notification > Thresholds</strong> page. <span class='english-translation'>The quality levels are determined by comparing sensor readings to pre-defined thresholds. You can view and edit these thresholds on the <strong>Alerts & Notification > Thresholds</strong> page.</span>"
        },
        {
            category: "Alerts & Notification",
            question: "Paano ako mag-set up ng bagong alert? <span class='english-translation'>How do I set up a new alert?</span>",
            answer: "Pumunta sa <strong>Alerts & Notification</strong> page at i-click ang <strong>Alert Rules</strong> tab para gumawa ng bagong rules para sa pag-trigger ng alerts. <span class='english-translation'>Go to the <strong>Alerts & Notification</strong> page and click on the <strong>Alert Rules</strong> tab to create new rules for triggering alerts.</span>"
        },
        {
            category: "Alerts & Notification",
            question: "Paano ko maa-adjust ang quality thresholds para sa alerts ko? <span class='english-translation'>How do I adjust the quality thresholds for my alerts?</span>",
            answer: "Sa <strong>Alerts & Notification</strong> page, mag-navigate sa <strong>Thresholds</strong> tab. Mula doon, pwede mong makita at i-edit ang pre-defined thresholds na nagde-determine ng quality levels. <span class='english-translation'>On the <strong>Alerts & Notification</strong> page, navigate to the <strong>Thresholds</strong> tab. From there, you can view and edit the pre-defined thresholds that determine quality levels.</span>"
        },
        {
            category: "Alerts & Notification",
            question: "Ano ang mangyayari kapag nag-trigger ang isang alert? <span class='english-translation'>What happens when an alert is triggered?</span>",
            answer: "May lalabas na live alert banner na may bell icon, na nagpapakita ng title at details ng bagong alert. Makakatanggap din kayo ng notifications batay sa inyong settings. <span class='english-translation'>A live alert banner will appear with a bell icon, showing the title and details of the new alert. You will also receive notifications based on your settings.</span>"
        },
        {
            category: "Alerts & Notification",
            question: "Pwede ko bang i-temporarily silence ang isang alert? <span class='english-translation'>Can I temporarily silence an alert?</span>",
            answer: "Oo, kapag lumabas ang live alert banner, pwede mong i-click ang 'Snooze' button para i-temporarily silence ito. <span class='english-translation'>Yes, when a live alert banner appears, you can click the 'Snooze' button to temporarily silence it.</span>"
        },
        {
            category: "Alerts & Notification",
            question: "Paano ko i-dismiss ang isang alert matapos ko itong na-address? <span class='english-translation'>How do I dismiss an alert after I have addressed it?</span>",
            answer: "Sa live alert banner, i-click ang 'Acknowledge' button para i-confirm na nakita at na-address mo na ang alert. <span class='english-translation'>On the live alert banner, click the 'Acknowledge' button to confirm you have seen and addressed the alert.</span>"
        },
        {
            category: "Alerts & Notification",
            question: "Saan ko makikita ang history ng lahat ng past alerts? <span class='english-translation'>Where can I see a history of all past alerts?</span>",
            answer: "Makikita mo ang kumpletong log ng lahat ng past alerts sa <strong>Alerts & Notification</strong> page sa ilalim ng <strong>Alert History</strong> tab. <span class='english-translation'>You can find a complete log of all past alerts on the <strong>Alerts & Notification</strong> page under the <strong>Alert History</strong> tab.</span>"
        },
        
        // Device & Sensor
        {
            category: "Device & Sensor",
            question: "Paano ko i-calibrate ang isang sensor? <span class='english-translation'>How do I calibrate a sensor?</span>",
            answer: "Pumunta sa <strong>Device & Sensor</strong> page. Sa 'Sensor Status & Calibration' card, hanapin ang sensor na gusto mong i-calibrate at i-click ang 'Calibrate' button para i-launch ang guided calibration wizard. <span class='english-translation'>Go to the <strong>Device & Sensor</strong> page. In the 'Sensor Status & Calibration' card, find the sensor you wish to calibrate and click the 'Calibrate' button to launch the guided calibration wizard.</span>"
        },
        {
            category: "Device & Sensor",
            question: "Paano ako mag-add ng bagong device sa system? <span class='english-translation'>How do I add a new device to the system?</span>",
            answer: "Ang <strong>Device & Sensor</strong> page ay may option para mag-add ng bagong devices. Kailangan mong ibigay ang unique ID ng device at iba pang detalye. <span class='english-translation'>The <strong>Device & Sensor</strong> page has an option to add new devices. You will need to provide the device's unique ID and other details.</span>"
        },
        {
            category: "Device & Sensor",
            question: "Saan ko makikita ang lokasyon ng aking devices? <span class='english-translation'>Where can I see the location of my devices?</span>",
            answer: "Ang <strong>Device & Sensor</strong> page ay may feature na map na nagpapakita ng geographical location ng lahat ng inyong connected devices. <span class='english-translation'>The <strong>Device & Sensor</strong> page features a map that shows the geographical location of all your connected devices.</span>"
        },
        {
            category: "Device & Sensor",
            question: "Paano ko makikita ang battery life ng device ko? <span class='english-translation'>How do I check the battery life of my device?</span>",
            answer: "Sa <strong>Device & Sensor</strong> page, pwede mong makita ang kasalukuyang battery status at power source (e.g., solar, AC adapter) para sa bawat connected device. <span class='english-translation'>On the <strong>Device & Sensor</strong> page, you can view the current battery status and power source (e.g., solar, AC adapter) for each connected device.</span>"
        },
        {
            category: "Device & Sensor",
            question: "Paano ko i-update ang firmware ng device ko? <span class='english-translation'>How do I update my device's firmware?</span>",
            answer: "Pwede kang mag-initiate ng firmware update mula sa <strong>Device & Sensor</strong> page. Ang system ang magga-guide sa inyo sa update process. <span class='english-translation'>You can initiate a firmware update from the <strong>Device & Sensor</strong> page. The system will guide you through the update process.</span>"
        },
        
        // User & System Management
        {
            category: "User & System Management",
            question: "Paano ko baguhin ang password ko? <span class='english-translation'>How do I change my password?</span>",
            answer: "Pwede mong baguhin ang password ninyo sa <strong>System Settings</strong> page sa ilalim ng 'Security' section. Kailangan mong i-enter ang inyong current password para mag-set ng bagong isa. <span class='english-translation'>You can change your password on the <strong>System Settings</strong> page under the 'Security' section. You will need to enter your current password to set a new one.</span>"
        },
        {
            category: "User & System Management",
            question: "Paano ko i-manage ang user accounts? <span class='english-translation'>How do I manage user accounts?</span>",
            answer: "Ang <strong>User Management</strong> page ay nagpapahintulot sa administrators na i-manage ang user accounts, kasama ang paggawa ng bagong users, pag-edit ng roles, at pag-manage ng permissions. <span class='english-translation'>The <strong>User Management</strong> page allows administrators to manage user accounts, including creating new users, editing roles, and managing permissions.</span>"
        },
        {
            category: "User & System Management",
            question: "Ano ang iba't ibang user roles? <span class='english-translation'>What are the different user roles?</span>",
            answer: "Sa <strong>User Management</strong> page, pwede mong makita at mag-assign ng iba't ibang roles sa users para i-control ang kanilang access levels sa loob ng system. <span class='english-translation'>On the <strong>User Management</strong> page, you can view and assign different roles to users to control their access levels within the system.</span>"
        },
        {
            category: "User & System Management",
            question: "Saan ko makikita ang log ng lahat ng user activities? <span class='english-translation'>Where can I view a log of all user activities?</span>",
            answer: "Ang <strong>Audit Log</strong> tab sa <strong>User Management</strong> page ay nagbibigay ng searchable history ng lahat ng user actions at system changes. <span class='english-translation'>The <strong>Audit Log</strong> tab on the <strong>User Management</strong> page provides a searchable history of all user actions and system changes.</span>"
        },
        {
            category: "User & System Management",
            question: "Paano ko baguhin ang system language? <span class='english-translation'>How do I change the system language?</span>",
            answer: "Pwede mong baguhin ang language ng system sa <strong>System Settings</strong> page sa ilalim ng <strong>General Settings</strong> tab. <span class='english-translation'>You can change the system's language on the <strong>System Settings</strong> page under the <strong>General Settings</strong> tab.</span>"
        },
        {
            category: "User & System Management",
            question: "Pwede ko bang i-customize ang dashboard? <span class='english-translation'>Can I customize the dashboard?</span>",
            answer: "Oo, ilang elements ng dashboard ay pwedeng i-customize mula sa <strong>System Settings</strong> page. <span class='english-translation'>Yes, some elements of the dashboard can be customized from the <strong>System Settings</strong> page.</span>"
        },
        
        // Glossary & Others
        {
            category: "Glossary & Others",
            question: "Ano ang TDS at Turbidity? <span class='english-translation'>What is TDS and Turbidity?</span>",
            answer: "<strong>TDS (Total Dissolved Solids)</strong> ay sumusukat sa kabuuang dami ng dissolved substances sa tubig, na kadalasang sinusukat sa parts per million (ppm). <strong>Turbidity</strong> ay sumusukat sa labo o haze ng tubig na sanhi ng suspended particles, na sinusukat sa Nephelometric Turbidity Units (NTU). <span class='english-translation'><strong>TDS (Total Dissolved Solids)</strong> measures the total amount of dissolved substances in the water, typically measured in parts per million (ppm). <strong>Turbidity</strong> measures the cloudiness or haziness of the water caused by suspended particles, measured in Nephelometric Turbidity Units (NTU).</span>"
        },
        {
            category: "Glossary & Others",
            question: "Ano ang pH at ano ang sinusukat nito? <span class='english-translation'>What is pH and what does it measure?</span>",
            answer: "<strong>pH</strong> ay sumusukat sa acidity o alkalinity ng tubig sa isang scale mula 0 hanggang 14. Ang pH na 7 ay neutral. <span class='english-translation'><strong>pH</strong> measures the acidity or alkalinity of the water on a scale from 0 to 14. A pH of 7 is neutral.</span>"
        },
        {
            category: "Glossary & Others",
            question: "Para saan ang Machine Learning page? <span class='english-translation'>What is the Machine Learning page for?</span>",
            answer: "Ang <strong>Machine Learning</strong> page ay kung saan pwede mong i-explore ang predictive analytics at trends sa inyong water quality data. <span class='english-translation'>The <strong>Machine Learning</strong> page is where you can explore predictive analytics and trends in your water quality data.</span>"
        },
    ];

    /**
     * Dynamically generates the FAQ accordion items, grouped by category.
     */
    function generateFaqs() {
        const faqContainer = document.getElementById('faq-container');
        if (!faqContainer) return;

        // Group FAQs by category
        const categories = faqs.reduce((acc, faq) => {
            const category = faq.category;
            if (!acc[category]) {
                acc[category] = [];
            }
            acc[category].push(faq);
            return acc;
        }, {});

        let faqHtml = '';
        for (const category in categories) {
            // Add a category header for each new section
            faqHtml += `<div class="faq-category-header"><h3>${category}</h3></div>`;

            // Add the accordion items for each FAQ in the category
            categories[category].forEach(faq => {
                faqHtml += `
                    <div class="settings-accordion-item">
                        <button class="settings-toggle-btn">${faq.question}<span class="arrow-icon"></span></button>
                        <div class="settings-content-panel">
                            <div class="content-card-inner">
                                <p>${faq.answer}</p>
                            </div>
                        </div>
                    </div>
                `;
            });
        }

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
            imageSrc: "static/profile/profile-christian.jpg",
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
            imageSrc: "static/profile/profile-clarence.jpg",
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
            imageSrc: "static/profile/profile-christianLuis.jpg",
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